from fastapi import File, UploadFile
from fastapi.responses import JSONResponse,FileResponse
# from fast_api import analysis
from models.video.emotion_recognition import onnx_inference
# from fast_api.analysis.eye_tracking import *  # ##############
# from fast_api.analysis.speech_analysis import *  # ##############
# from fast_api.summarization.text_summarization import *
from fastapi import HTTPException

from models.video.eye_tracking.example import analyze_gaze
#from fastapi.middleware.cors import CORSMiddleware

from audio_util import extract_audio
from models.speech.speech_analysis import *

import numpy as np
import cv2
import tempfile
import os 


async def analyze_file(file: UploadFile):
    if file.filename.endswith(".mp4"):
        # emotion recognition task
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
            tmp_img.write(np_arr)
            tmp_img_path = tmp_img.name
        cap = cv2.VideoCapture(tmp_img_path)  # VideoCapture object
        tmp_img.close()
        os.unlink(tmp_img_path)


        emotion_list = onnx_inference.emotions_detector(cap)
        emotion_result = onnx_inference.emotion_detection_result(emotion_list)

        # eye tracking task
        try:
            video_path = file.filename
            with open(video_path, "wb") as video:
                video.write(file.file.read())
            output_path='ouput2.mp4'
        
            gaze_result = analyze_gaze(video_path,output_path)

            # return result

        except Exception as e:
            print(f"An error occurred: {e}")
            return JSONResponse(content={"error": str(e)}, status_code=500)
        
        
        # speech analysis task
        audio_file = extract_audio(file)
        stt_result = perform_stt(audio_file)
        if isinstance(stt_result, tuple):
            stt_text = stt_result[1]  # Extract the text from the result
        else:
            stt_text = stt_result  # Directly use the result if it's not a tuple
        speech_speed = analyze_speed(audio_file, stt_text)
        num_pauses, pause_durations = detect_pause(audio_file)
        filler_words = detect_korean_filler_words(stt_text)
        os.remove(audio_file)
        
        # speech_result = analyze_speech(file.file)  # ##############
        return JSONResponse(content={"emotion": emotion_result, "gaze":gaze_result, "speed": speech_speed,
                            "pauses": num_pauses, "durations": pause_durations, "filler": filler_words})  # ##############, "speech": speech_result}
    # elif file.filename.endswith((".txt", ".pdf", ".doc", ".docx")):
    #     summarized_text = summarize_text(file.file)
    #     return JSONResponse(content={"summarized_text": summarized_text})
    else:
        raise HTTPException(
            status_code=415, detail='Unsupported file format'
        )