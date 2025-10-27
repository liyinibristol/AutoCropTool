- Run `./utils/REDline.py` to parse the raw video data
  - Step 1: Adapt the input and output directories to your data.
  ```python
    # ISO = 12800 # 800 for normal light, 12800 for low light
    low_input_dir = r"/data2/B003"
    low_output_dir = r"/data1/Dataset/Esprit/Video_frames/Low_light"
    batch_process(low_input_dir, low_output_dir, 12800, is_flip=True)

    normal_input_dir = r"/data2/A003"
    normal_output_dir = r"/data1/Dataset/Esprit/Video_frames/Normal_light"
    batch_process(low_input_dir, low_output_dir, 800, is_flip=False)
    ```

  - Step 2: Rename the name of frames to align the timestamp at each frame. Code will read the `Offset_TC_*.txt` to get the first frame index.  

    ```python
    data_dir = Path(r"/data1/Dataset/Esprit/Video_frames")
    offset_file_path = Path(r"/data1/Dataset/Esprit/Offset_TC_003.txt")
    low_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Low_light")
    normal_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Normal_light")
    frms_post_processing(normal_dir, low_dir, offset_file_path)
    ```

- If run `./main.py`, please make sure the environment meets the `requirement.txt`.