import cv2
import os
from pathlib import Path

import pandas as pd
import numpy as np
import ffmpeg

from typing import Tuple


def video_info(video_path: str) -> Tuple[int, int, int]:
    """
    Uses the ffmpeg.probe function to retrieve information about a video file.

    :param video_path: Path to a valid video file
    :return: A 3-tuple with integers for (width, height, number_of_frames)
    """

    #
    # Fetch video info
    info = ffmpeg.probe(video_path)
    # Get the list of all video streams
    video_streams = [stream for stream in info['streams'] if stream['codec_type'] == 'video']
    if len(video_streams) == 0:
        raise BaseException("No video streams found in file '{}'".format(video_path))

    # retrieve the first stream of type 'video'
    info_video = video_streams[0]

    video_w = info_video['width']
    video_h = info_video['height']
    n_frames = int(info_video['nb_frames'])

    return video_w, video_h, n_frames


def extract_frames(video_file: str, timestamps_df: pd.DataFrame, output_dir: str):

    #_, _, num_frames = video_info(video_file)
    #print("NUM:", num_frames, len(timestamps_df))

    # Open the video file
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        raise Exception(f"Couldn't open video file '{video_file}'")

    first_col_name = timestamps_df.columns[0]
    timestamps: pd.Series = timestamps_df[first_col_name]

    # Loop over each timestamp in the CSV file
    for fnum, timestamp in enumerate(timestamps):
        # Extract the frame using OpenCV
        #cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_dir, str(timestamp) + ".jpg")
            cv2.imwrite(frame_path, frame)
        else:
            print(f"At frame {fnum}, no more frames to extract from video '{video_file}'. Expected {len(timestamps)} frames.")
            #raise Exception(f"At frame {fnum}, no more frames to extract from video '{video_file}'. Expected {len(timestamps)} frames.")
    
    # Release the video file
    cap.release()


def rebuild_video(dir: Path, frames: pd.DataFrame, outfile: Path) -> None:

    # We don't know the target video size, yet.
    frame_width = None
    frame_height = None

    # It will be instantiated later, after we know the size of the first image
    ffmpeg_video_out_process = None

    for idx, row in frames.iterrows():
        ts = row["timestamp"]
        gen = row["generated"]

        if gen == "Original":

            frame_path = dir / (str(ts) + ".jpg")

            if not frame_path.exists():
                print(f"Skipping frame {str(frame_path)}")
                continue            # BEWARE! Continues the cycle

            img_bgr = cv2.imread(str(frame_path))
            img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # If the frame size was not determined yet, take it from the next picture and initialize the ffmpeg encoder
            if frame_width is None:
                assert frame_width is None and frame_height is None and ffmpeg_video_out_process is None

                frame_height, frame_width, _ = img.shape
                font_width = int(frame_height * 0.04)
                ffmpeg_video_out_process = (
                                    ffmpeg
                                        .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(frame_width, frame_height))
                                        # -vf "drawtext=fontfile=Arial.ttf: fontsize=48: text=%{n}: x=(w-tw)/2: y=h-(2*lh): fontcolor=white: box=1: boxcolor=0x00000099"
                                        .drawtext(text="%{n}", escape_text=False,
                                                  #x=50, y=50,
                                                  x="(w-tw)/2", y="h-(2*lh)",
                                                  fontfile="Arial.ttf", fontsize=font_width, fontcolor="white",
                                                  #boxcolor="0x00000099",
                                                  box=1, boxborderw=2, boxcolor="Black@0.6")

                                        .output(str(outfile), pix_fmt='yuv420p')

                                    .overwrite_output()
                                    .run_async(pipe_stdin=True)
                                )

            assert frame_width is not None and frame_height is not None and ffmpeg_video_out_process is not None

            # Send the frame to the ffmpeg process
            ffmpeg_video_out_process.stdin.write(img.tobytes())

        elif gen == "Generated":

            # The first frame can NOT be a generated one
            assert frame_width is not None and frame_height is not None

            # Create an artificial black frame
            print(f"Injecting Black frame at idx {idx}")
            black_frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
            ffmpeg_video_out_process.stdin.write(black_frame.tobytes())

        else:
            raise Exception(f"Unexpected value '{gen}' in column 'generated' at index {idx}")

    # Close the video stream
    if ffmpeg_video_out_process is not None:
        ffmpeg_video_out_process.stdin.close()
        ffmpeg_video_out_process.wait()
        ffmpeg_video_out_process = None
