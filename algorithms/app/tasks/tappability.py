from urllib import response
from PIL import Image
import json
import os
from resources.resource import *
from resources.screenshot import *
from tasks.task import Task
from typing import List, Callable, Tuple
import shutil
import subprocess

class Tappability(Task):
    """Class for managing Tappability algorithm"""
    
    def __init__(self, output_dir, resource_dict) -> None:
        super().__init__(output_dir, resource_dict)
        self.img_lst = {}
        self.running = False
        self.threshold = 50
        print("tappability")
        self._sub_to_new_image()
        
    @classmethod
    def get_name(cls) -> str:
        """Name of the task"""
        return Tappability.__name__
    
    @classmethod
    def get_input_types(cls) -> List[ResourceType]:
        return [Screenshot]


    @classmethod
    def get_output_types(cls) -> List[ResourceType]:
        return [Screenshot]

        
    def _sub_to_new_image(self) -> None:
        """Get notified when new activity is added"""
        self.resource_dict['UI_Info'].subscribe(tappable_callback)
    
    def tappable_callback(self, new_img: Screenshot) -> None:
         """Callback method to add img and run converter method"""
         if new_img.get_view_name() not in self.img_lst:
             self._add_img(new_img)
             self._process_img()

    def _add_img(self, img: Screenshot) -> None:
        """Add img to img list"""
        view_name = img.get_view_name()
        if view_name not in self.img_lst:
            self.img_lst[view_name] = {"item": img, "is_completed": False, "ready": False}
            
    def _get_next(self) -> Screenshot:
        """Get next img from list which is uncompleted"""
        img_lst = [val["item"] for val in self.img_lst.values() if not val["is_completed"] and not val["item"].gget_tappability_path()]
        return img_lst[0] if len(img_lst) > 0 else None

    def _process_img(self) -> None:
        """Check to see if json is available. Process image or subscribe to json"""
        next_img = self._get_next()
        self.img_lst[next_img.get_view_name()]["ready"] = True # set ready
        self._run()
    
    def _move_items(self, path:str) -> list:
        """Move ready items into temp directory"""
        if not os.path.exists(path):
            os.makedirs(path)
            os.makedirs(os.path.join(path, 'images'))
            os.makedirs(os.path.join(path, 'annotations'))
        item_ready = []
        for val in self.img_lst.values():
            if not val["is_completed"] and val["ready"]:
                item = val["item"]
                shutil.copy(item.get_image_files['jpeg'], os.path.join(path, 'images', item.get_view_name() + ".jpeg"))
                shutil.copy(item.get_layout_files['json'], os.path.join(path, 'annotations', item.get_view_name() + ".json"))
                item_ready.append(val["item"])
        return item_ready
            
    def _run(self) -> None:
        """Run tappable on temp batch"""
        if not self.running:
            self.running = True
            path = os.path.join(self.output_dir + "temp_dir")
            item_lst = self._move_items(path)
            #run tappable
            subprocess.call(['python3','PATH TO TAPPABLE', '-i', os.path.join(path, 'images'), '-x', os.path.join(path, 'annotations'), '-o', self.output_dir, '-t', str(self.threshold)])
            #publish
            self._publish(item_lst, path)
    
    def _publish(self, item_lst: list, path: str) -> None:
        """publishes and updates item"""
        for item in item_lst:
            #set item as complete 
            self.img_lst[item.get_view_name()]["is_completed"] = True
            item.set_tappability_path(os.path.join(path, item.get_view_name()))
        #clear temp folder
        shutil.rmtree(os.path.join(path, 'images'))
        shutil.rmtree(os.path.join(path, 'annotations'))
        os.makedirs(os.path.join(path, 'images'))
        os.makedirs(os.path.join(path, 'annotations'))
        #set tappability as not running
        self.running = False
                    
    def is_complete(self):
        """Checks if all images in list have been convertered"""
        if self._get_next() == None:
            return True
        else:
            return False  
        
    def get_tappability_predictions(self) -> str:
        # run xbot and droidbot if not already run
        self._run_image_algorithms()
        # copy screenshots into temp folder convert PNGs to JPEG & get annotations
        img_path = os.path.join(TEMP_PATH,"tappability", "screenshots")
        json_path = os.path.join(TEMP_PATH,"tappability", "annotations")
        self._move_files_xb(img_path, json_path, jpg=True)
        self._move_files_db(img_path, json_path)
        # run tappability
        tappability = Tappability(img_path, json_path, os.path.join(self.output_dir,"tappability"), threshold=50)
        self.execute_task(tappability)
        # copy results into activity folders
        self._get_ui_display_issues(tappability=True)
        return None

    def _get_ui_display_issues(self, tappability = False, owleye = False, xbot=False):
        """Separates display issues by activity per algorithm"""
        activites_path = os.path.join(self.output_dir, "activities")
        for activity_name in list(set(self.activity_list)):
            tap_temp_path = os.path.join(TEMP_PATH, "tappability", activity_name)
            if tappability and os.path.exists(tap_temp_path):
                tap_path = os.path.join(activites_path, activity_name, "tappability_prediction")
                if not os.path.exists(tap_path):
                    os.makedirs(tap_path)
                for file in os.listdir(tap_temp_path):
                    shutil.copy(os.path.join(tap_temp_path, file), os.path.join(activites_path, activity_name, "tappability_prediction"))
            if owleye and os.path.exists(os.path.join(TEMP_PATH, "owleye", activity_name + '.jpg')):
                if not os.path.exists(os.path.join(activites_path, activity_name, "display_issues")):
                    os.makedirs(os.path.join(activites_path, activity_name, "display_issues"))
                shutil.copy(os.path.join(TEMP_PATH, "owleye", activity_name + '.jpg'), os.path.join(activites_path, activity_name,"display_issues"))
            return None