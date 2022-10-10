from models.screenshot import Screenshot
from models.emulator import Emulator
from tasks.task import *
from resources.resource import *
from typing import List, Dict, Tuple
import os


class Xbot(Task):
    """Class for managing Xbot algorithm"""
    
    _input_types = [ResourceType.APK_FILE, ResourceType.EMULATOR]
    _output_types = [ResourceType.SCREENSHOT, ResourceType.ACCESSIBILITY_ISSUE]
    _url = 'http://host.docker.internal:3003/execute'
    
    def __init__(self, output_dir, resource_dict : Dict[ResourceType, ResourceGroup], uuid: str) -> None:
        super().__init__(output_dir, resource_dict, uuid)
        self.apk_queue = {}
        self._sub_to_apks()
        self._sub_to_emulators()

    @classmethod
    def get_name(cls) -> str:
        """Name of the task"""
        return Xbot.__name__
    
    @classmethod
    def get_input_types(cls) -> List[ResourceType]:
        """Input resource types of the task"""
        return Xbot._input_types

    @classmethod
    def get_output_types(cls) -> List[ResourceType]:
        """Output resource types of the task"""
        return Xbot._output_types
    
    @classmethod
    def run(cls, apk_path: str, output_dir: str, emulator: str) -> None:
        """Runs Xbot"""
        data = {
            "apk_path": apk_path,
            "output_dir": output_dir,
            "emulator": emulator
        }
        
        Xbot.http_request(Xbot._url, data)
    
    
    def _sub_to_apks(self) -> None:
        """Get notified when a new APK is available"""
        if ResourceType.APK_FILE in self.resource_dict:
            self.resource_dict[ResourceType.APK_FILE].subscribe(self.apk_callback) # calls add_apk() when new apk is available
            
            
    def _sub_to_emulators(self) -> None:
        """Get notified when an emulator is available"""
        if ResourceType.EMULATOR in self.resource_dict:
            self.resource_dict[ResourceType.EMULATOR].subscribe(self.emulator_callback)
    
    
    def _process_apks(self, emulator: Emulator) -> None:
        """Process apks"""
        
        print("XBOT RUNNING")

        while len(self.apk_queue) > 0:                              # get next apk
            apk = self.apk_queue.keys()[0]

            apk_path = apk.get_path()
            Xbot.run(apk_path, self.output_dir, emulator.connection_str)      # run algorithm
            self._publish_outputs()                                # dispatch results

            self.apk_queue[apk] = True

        print("XBOT COMPLETED")
        
    
    
    def apk_callback(self, new_apk : ResourceWrapper) -> None:
        """callback method to add apk and run algorithm"""
        if new_apk not in self.apk_queue:
            self.apk_queue[new_apk] = False

    
    def emulator_callback(self, emulator : ResourceWrapper) -> None:
        """callback method for using emulator"""
        
        self._process_apks(emulator=emulator.get_metadata())
        emulator.release()
    
    
    def is_complete(self) -> bool:
        for status in self.apk_queue.values():
            if not status:
                return False 
            
        return self.resource_dict[ResourceType.APK_FILE].is_active()
    
    
    def _publish_outputs(self) -> None:
        """Dispatch all outputs for processed apk"""
        screenshots = self._get_screenshots()
        issues = self._get_accessibility_issues()
        
        complete = False
        for screenshot in screenshots:
            if screenshot == screenshots[:-1]:
                complete = self.is_complete()
            rw = ResourceWrapper(None, self.get_name(), screenshot)
            self.resource_dict[ResourceType.SCREENSHOT].publish(rw, complete)
        
        complete = False
        for issue in issues:
            if screenshot == issues[:-1]:
                complete = self.is_complete()
            rw = ResourceWrapper(None, self.get_name(), issue)
            self.resource_dict[ResourceType.ACCESSIBILITY_ISSUE].publish(rw, complete)
    
    
        
    def _get_accessibility_issues(self) -> List[Tuple[Screenshot, str, str]]:
        """ Gets list of accessibility issues from xbot output directory. 
            Returns list of tuples containing (original screenshot, image path, description path)        
        """
        screenshots = self._get_screenshots()
        issues = []
        issues_dir = os.path.join(self.output_dir, "issues")

        # folder name = activity name 
        for screenshot in screenshots:
            activity = screenshot.ui_screen                    
            image_path = os.path.join(issues_dir, activity, activity + ".png")
            desc_path = os.path.join(issues_dir, activity, activity + ".txt")
            if os.path.exists(image_path) and os.path.exists(desc_path):
                issues.append((screenshot, image_path, desc_path))             
        return issues

    def _get_screenshots(self) -> List[Screenshot]:
        """ Gets list of screenshot images and layouts from xbot output directory.
            Returns list of tuples containing (activity name, image path, layout path)
        """
        screenshots = []
        images_dir = os.path.join(self.output_dir, "screenshot")     
        layouts_dir = os.path.join(self.output_dir, "layouts")
        
        for activity in os.listdir(images_dir):
            layout_path = os.path.join(layouts_dir, activity + ".xml")
            # select image file which is not the thumbnail 
            for filename in os.listdir(os.path.join(images_dir, activity)):
                if len(filename) > 14 and filename[-14:-5] != "_thumbnail":
                    image_path = os.path.join(images_dir, activity, activity+'.png')
                    os.rename(os.path.join(images_dir, activity, filename), image_path) # rename screenshot to same name as layout file
                    screenshots.append(Screenshot(activity, image_path, layout_path))
                    break      
        return screenshots