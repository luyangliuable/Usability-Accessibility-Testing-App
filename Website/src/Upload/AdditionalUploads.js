import React, { useEffect, useState } from 'react'
import { Container } from "react-bootstrap";
import { Link, useLocation, useNavigate } from 'react-router-dom';

import './Upload.css';
import '../components/button.css';

import UploadBox from "./components/UploadBox";

import {
  Accordion,
  AccordionItem,
  AccordionItemHeading,
  AccordionItemButton,
  AccordionItemPanel,
} from 'react-accessible-accordion';

const AdditionalUploads = () => {
  const [currentAppStatus, updateCurrentAppStatus] = useState("READY");

  const locations = useLocation();
  const navigate = useNavigate();

  console.log("[0] load state")
  const tempState = locations.state?.objectState;
  const [objectState, setObjectState] = useState(tempState);
  console.log(objectState);

  const algorithms = typeof objectState === "undefined" ? [] : objectState.algorithms;

  useEffect(() => {
    if (typeof objectState === "undefined") {
      console.log("[1.2] redirect")
      navigate("/upload");
    }
  }, [objectState, navigate]);

  const selectedAlgorithms = [];
  for (let i = 0; i < algorithms.length; i++) {       // Extracts selected algorithms that require additional uploads from the algorithms data structure
    if (algorithms[i].selected === true && algorithms[i].requiresAdditionalInput === true) {
      selectedAlgorithms.push(algorithms[i]);
    }
  }
  console.log(selectedAlgorithms);

  const [buttonState, setButtonState] = useState(true);
  const [algorithmCount, setAlgorithmCount] = useState(new Array(selectedAlgorithms.length).fill(true));
  console.log(algorithmCount);

  const uploadState = (state) => {
    for (var i = 0; i < objectState.algorithms.length; i++) {
      if (objectState.algorithms[i].uuid === state.requester.algorithm) {
        objectState.algorithms[i].additionalFiles.push(state.selectedFile);
      }
    }
    setObjectState(objectState);
    algorithmCount[state.requester.index] = state.buttonState;
    if (algorithmCount.every(element => element === false)) {
      setButtonState(false)
    }
    else {
      setButtonState(true);
    }
  }

  return (
    <Container className='container-nav'>
      <div className="upload-root">

        <p className="upload-text-60 upload-text-center">ADDITIONAL UPLOADS</p>
        <p className="upload-text-30 upload-text-center">Upload additional files to evaluated for bugs</p>

        <div className="upload-vspacing-40"> </div>

        {/* If there are algorithms that require additional uploads, i.e. selectedAlgoriithms.length > 0, it will render the accordions. Otherwise, it will render the text layed out in the divs below */}
        {selectedAlgorithms.length ?
          <div>
            < Accordion allowZeroExpanded allowMultipleExpanded >
              {selectedAlgorithms.map((algorithm, index) => {
                // If any of the selected algorithms require an additional upload it will generate accordions with an upload box for it
                return (
                  <AccordionItem key={algorithm.uuid}>
                    <AccordionItemHeading>
                      <AccordionItemButton>
                        {algorithm.algorithmName}
                      </AccordionItemButton>
                    </AccordionItemHeading>
                    <AccordionItemPanel>
                      <UploadBox currentAppStatus={currentAppStatus} updateCurrentAppStatus={updateCurrentAppStatus} acceptedFileTypes={algorithm.additionalInputFileTypes} method={uploadState} requester={{ algorithm: algorithm.uuid, index: index }} />
                    </AccordionItemPanel>
                  </AccordionItem>
                )
              })
              }
            </Accordion >
          </div> :
          <div>
            <p className="upload-text-30 upload-text-center">
              None of the selected algorithms require an additional upload.
            </p>
          </div>
        }

        <div className="upload-vspacing-40"> </div>

        <div className="next-button-align-right" >
          <Link to={"/upload/summary"} style={buttonState ? { pointerEvents: 'none' } : {}} state={{ objectState: objectState }}>
            <button disabled={buttonState}>
              <h3>NEXT</h3>
            </button>
          </Link>
        </div>

      </div>
    </Container>
  );
}

export default AdditionalUploads;
