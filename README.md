
### Processing Video Data

To extract and process video frames, follow the steps below:

#### 1. Run `./utils/REDline.py`

This script processes raw video data into individual frames.

**Step 1: Configure Input and Output Paths**  
Modify the input and output directories according to your data structure:

```python
# ISO = 12800  # Use 800 for normal light, 12800 for low light

# Process low-light videos
low_input_dir = r"/data2/B003"
low_output_dir = r"/data1/Dataset/Esprit/Video_frames/Low_light"
batch_process(low_input_dir, low_output_dir, 12800, is_flip=True)

# Process normal-light videos
normal_input_dir = r"/data2/A003"
normal_output_dir = r"/data1/Dataset/Esprit/Video_frames/Normal_light"
batch_process(normal_input_dir, normal_output_dir, 800, is_flip=False)
```

**Step 2: Align Frames by Timestamp**  
Rename frames to align timestamps using the corresponding offset file (located in `./utils`):

```python
data_dir = Path(r"/data1/Dataset/Esprit/Video_frames")
offset_file_path = Path(r"/data1/Dataset/Esprit/Offset_TC_003.txt")
low_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Low_light")
normal_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Normal_light")
frms_post_processing(normal_dir, low_dir, offset_file_path)
```

#### 2. Run `./main.py`

- **Option 1:** Before executing `main.py`, ensure your environment meets the dependencies listed in `requirements.txt`.
