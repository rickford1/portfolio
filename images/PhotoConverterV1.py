'''Written and designed by Rick Friedman Fall of 2024
Intended for use with modified ENDER 3 V2
**AI was used for debugging -- Simplification of code**

 Refer to TwelvePensV5Working.py for more in depth commenting and documentation'''













import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import sys
import shutil


# Import Image and Convert to CMYK
#originalInput = Image.open('input_image.jpg')
originalInput = Image.open('input_image.jpg')
cmyk_img = originalInput.convert("CMYK")

# Find size of input Image -- For testing
width1, height1 = cmyk_img.size
print(f' Original Image size: {width1}x{height1} pixels')

# Convert size to 600x600
square_img = cmyk_img.resize((600, 600))
square_img.show()

# Turn pixel data into a number matrix
width2, height2 = square_img.size
pixels = list(square_img.getdata())
square_matrix = []

for y in range(height2):
    row = pixels[y * width2:(y + 1) * width2]
    square_matrix.append(row)

# Display first 6x6 for testing
#for row in square_matrix[:6]:  # Print the first 6 rows
    #print(row[:6])

# Find most prominent color, set that to the new value
prominent_color_matrix = []

rows = square_matrix

for row in rows:
    quads = row
    prominent_color_row = []
    for quad in quads:

        # Check if all CMYK values are less than 200 set equal to white
        if all(value < 120 for value in quad):
            prominent_color_row.append([0, 0, 0, 0])  # White in CMYK

        # Check if three or more CMYK values are greater than 150 (black)
        elif sum(value > 120 for value in quad) >= 3:
            prominent_color_row.append([0, 0, 0, 255])  # Black in CMYK

        else:
            max_color = [-1, -1]  # [color value, index of max color]
            for i, color in enumerate(quad):
                if max(max_color[0], color) == color:
                    max_color = (color, i)
            # Map the index of the maximum color to CMYK values
            if max_color[1] == 0:
                prominent_color_row.append([255, 0, 0, 0])  # Cyan in CMYK
            elif max_color[1] == 1:
                prominent_color_row.append([0, 255, 0, 0])  # Magenta in CMYK
            elif max_color[1] == 2:
                prominent_color_row.append([0, 0, 255, 0])  # Yellow in CMYK
            elif max_color[1] == 3:
                prominent_color_row.append([0, 0, 0, 255])  # Black in CMYK
            else:
                print("Error", quad)
    prominent_color_matrix.append(prominent_color_row)

# Convert the prominent_color_matrix to a NumPy array
prominent_color_array = np.array(prominent_color_matrix, dtype=np.uint8)

# Create an image from the NumPy array
prominent_color_img = Image.fromarray(prominent_color_array, 'CMYK')

# Display the image
prominent_color_img.show()

#print(prominent_color_array)










#Trying to resize the image

# Resize the image to 100x100, averaging 6x6 blocks
new_size = 100
block_size = 6

# Prepare to create the new 100x100 image
new_matrix = []

for y in range(new_size):
    new_row = []
    for x in range(new_size):
        # Calculate the coordinates of the 6x6 block
        start_x = x * block_size
        start_y = y * block_size
        end_x = start_x + block_size
        end_y = start_y + block_size
        
        # Get the block of pixels
        block = [prominent_color_matrix[j][start_x:end_x] for j in range(start_y, end_y)]
        block = [pixel for row in block for pixel in row]  # Flatten the block
        
        # Calculate the average color for the block
        block_array = np.array(block, dtype=np.uint8)
        avg_color = np.mean(block_array, axis=0).astype(np.uint8)
        
        # Append the average color to the new row
        new_row.append(avg_color.tolist())
    
    new_matrix.append(new_row)

# Convert the new matrix to a NumPy array
new_array = np.array(new_matrix, dtype=np.uint8)

# Create an image from the NumPy array
resized_img = Image.fromarray(new_array, 'CMYK')

# Display the image
resized_img.show()


# Convert new_array to the desired format: single index per cell
index_only_matrix = []

for row in new_array:
    index_only_row = []
    for cell in row:
        # Check if all CMYK values in the cell are zero
        if all(value == 0 for value in cell):
            index_only_row.append(4)  # Replace with 5 if all values are zero
        else:
            # Find the index of the non-zero value
            non_zero_indices = [i for i, value in enumerate(cell) if value > 0]
            if len(non_zero_indices) == 1:
                index_only_row.append(non_zero_indices[0])
            else:
                # If more than one non-zero value, use the first non-zero index for simplicity
                index_only_row.append(non_zero_indices[0])
    index_only_matrix.append(index_only_row)

# Convert the index_only_matrix to a NumPy array
index_only_array = np.array(index_only_matrix, dtype=np.uint8)

print(f'New Image Size: {index_only_array.shape}')
np.set_printoptions(threshold=sys.maxsize)
print(index_only_array[0])


#Splitting into four seperate arrays, with a value of 1 if there should be a dot in that position and 0 if not

# Initialize the four arrays
array_c = np.zeros_like(index_only_array, dtype=np.uint8)     
array_m = np.zeros_like(index_only_array, dtype=np.uint8)
array_y = np.zeros_like(index_only_array, dtype=np.uint8)
array_k = np.zeros_like(index_only_array, dtype=np.uint8)

# Populate the arrays
array_c[index_only_array == 0] = 1
array_m[index_only_array == 1] = 1
array_y[index_only_array == 2] = 1
array_k[index_only_array == 3] = 1

print(array_y[0])





#Converting Image to base G-Code ALL VALUES IN ABSOLUTE POSITIONING!!!!!!!!!
#Start with cyan as initial color

# Define initial start and end points for x and y
x_start_initial = 50
x_end_initial = 150
y_start_initial = 150
y_end_initial = 50

# Define file names
start_filename = 'gcode_start.txt'
output_filename = 'gcode_output.txt'
temp_filename = 'gcode_temp.txt'

# Read the content of gcode_start.txt --- Starts with pen lifted in Z-Axis
try:
    with open(start_filename, 'r') as start_file:
        start_content = start_file.read()
except IOError as e:
    print(f"Error reading start file: {e}")
    raise

# Generate G-Code and save to a temporary file for all four colors
try:
    with open(temp_filename, 'w') as temp_file:
        # Write the start content first
        temp_file.write(start_content)

        # Process Cyan
        x_start = x_start_initial
        x_end = x_end_initial
        y_start = y_start_initial
        y_end = y_end_initial
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end - 1, -1):
                x_index = x - x_start_initial
                y_index = y_start_initial - y
                
                if 0 <= x_index < len(array_c) and 0 <= y_index < len(array_c[0]):
                    if array_c[x_index][y_index] == 1:
                        temp_file.write(f"G0 F6000 X{x} Y{y}\n")    #Go to location
                        temp_file.write(f"G0 F6000 Z0.1\n")              #Tap pen at location
                        temp_file.write(f"G0 F6000 Z3\n")                #Lift pen before linear movement


        #Turn extruder in order to load next color (magenta)
        temp_file.write(f"G0 F2000 Z50\n")         #Lift extruder before rotation
        temp_file.write(f"M302 P1\n")         #Enable extruder/disable heat check
        temp_file.write(f"G1 F200 E8.5\n")    #Rotate extruder/Switch Color
        temp_file.write(f"M302 P0\n")         #Disable extruder/enable heat cheack


        # Reset values before processing the next color
        x_start = x_start_initial
        x_end = x_end_initial
        y_start = y_start_initial
        y_end = y_end_initial

        # Process Magenta
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end - 1, -1):
                x_index = x - x_start_initial
                y_index = y_start_initial - y
                
                if 0 <= x_index < len(array_m) and 0 <= y_index < len(array_m[0]):
                    if array_m[x_index][y_index] == 1:
                        temp_file.write(f"G0 F6000 X{x} Y{y}\n")
                        temp_file.write(f"G0 F6000 Z0.1\n")
                        temp_file.write(f"G0 F6000 Z3\n")


        #Turn extruder in order to load next color (Yellow)
        temp_file.write(f"G0 F2000 Z50\n")         #Lift extruder before rotation
        temp_file.write(f"M302 P1\n")         #Enable extruder/disable heat check
        temp_file.write(f"G1 F200 E17\n")    #Rotate extruder/Switch Color
        temp_file.write(f"M302 P0\n")         #Disable extruder/enable heat cheack

        # Reset values before processing the next color
        x_start = x_start_initial
        x_end = x_end_initial
        y_start = y_start_initial
        y_end = y_end_initial

        # Process Yellow
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end - 1, -1):
                x_index = x - x_start_initial
                y_index = y_start_initial - y
                
                if 0 <= x_index < len(array_y) and 0 <= y_index < len(array_y[0]):
                    if array_y[x_index][y_index] == 1:
                        temp_file.write(f"G0 F6000 X{x} Y{y}\n")
                        temp_file.write(f"G0 F6000 Z0.1\n")
                        temp_file.write(f"G0 F6000 Z3\n")




		#Turn extruder in order to load next color (Black)
        temp_file.write(f"G0 F2000 Z50\n")         #Lift extruder before rotation
        temp_file.write(f"M302 P1\n")         #Enable extruder/disable heat check
        temp_file.write(f"G1 F200 E25.5\n")    #Rotate extruder/Switch Color
        temp_file.write(f"M302 P0\n")         #Disable extruder/enable heat cheack




        # Reset values before processing the next color
        x_start = x_start_initial
        x_end = x_end_initial
        y_start = y_start_initial
        y_end = y_end_initial

        # Process Black
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end - 1, -1):
                x_index = x - x_start_initial
                y_index = y_start_initial - y
                
                if 0 <= x_index < len(array_k) and 0 <= y_index < len(array_k[0]):
                    if array_k[x_index][y_index] == 1:
                        temp_file.write(f"G0 F6000 X{x} Y{y}\n")
                        temp_file.write(f"G0 F6000 Z0.1\n")
                        temp_file.write(f"G0 F6000 Z3\n")


        #Turn extruder to original color/cyan
        temp_file.write(f"G0 F2000 Z50\n")         #Lift extruder before rotation
        temp_file.write(f"M302 P1\n")         #Enable extruder/disable heat check
        temp_file.write(f"G1 F200 E34\n")    #Rotate extruder/Switch Color
        temp_file.write(f"M302 P0\n")         #Disable extruder/enable heat cheack



except IOError as e:
    print(f"Error writing to temporary file: {e}")
    raise

# Replace the original output file with the temporary file
try:
    shutil.move(temp_filename, output_filename)
except IOError as e:
    print(f"Error moving temporary file to output file: {e}")
    raise