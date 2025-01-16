import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
from PIL import Image
from matplotlib.animation import FuncAnimation, FFMpegWriter
import streamlit as st
import tempfile
import os
from IPython.display import Video

# ตั้งค่า seed สำหรับการสุ่ม
np.random.seed()

# --- แสดงหัวข้อ ---
st.title('Simulation of Fire Spread Based on Terrain Slope')

# --- อัปโหลดไฟล์ภาพ ---
uploaded_file = st.file_uploader("Upload Image (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img_array = np.array(img)
    st.image(img, caption='Uploaded Image', use_container_width=True)

    # ฟังก์ชันแปลงสีในภาพเป็นค่าความลาดชัน
    def map_color_to_slope(img_array):
        slope_map = {
            (144, 238, 144): 5,    # เขียวอ่อน (0-5%)
            (255, 218, 185): 15,   # ส้มอ่อน (5.1-15%)
            (255, 160, 122): 25,   # ส้มเข้ม (15.1-25%)
            (255, 99, 71): 35,     # แดง (25.1-35%)
            (178, 34, 34): 100     # แดงเข้ม (35.1-100%)
        }
        colors = np.array(list(slope_map.keys()))
        slope_values = np.array(list(slope_map.values()))
        kdtree = KDTree(colors)
        reshaped_img = img_array[:, :, :3].reshape(-1, 3)
        _, nearest_index = kdtree.query(reshaped_img)
        slope = slope_values[nearest_index].reshape(img_array.shape[0], img_array.shape[1])
        return slope

    # --- แสดงแผนที่ความลาดชัน ---
    terrain_slope = map_color_to_slope(img_array)

    def display_slope_grid(slope):
        cmap = plt.get_cmap("YlGn")  # ใช้แผนที่สีเขียว-ส้ม
        plt.figure(figsize=(8, 6))
        plt.imshow(slope, cmap=cmap, interpolation='bilinear')  # ใช้ interpolation แบบ bilinear เพื่อให้กริดดูเนียนขึ้น
        plt.colorbar(label='Slope (%)')
        plt.title("Terrain Slope Map")
        plt.axis('off')
        st.pyplot(plt)

    display_slope_grid(terrain_slope)

    # --- รับค่าความเร็วลมและทิศทางลมจากผู้ใช้ ---
    wind_speed = st.slider("Wind Speed (km/hr)", min_value=0, max_value=100, value=30)
    wind_direction = st.selectbox("Wind Direction", ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW'])

    # --- ค่าคงที่สำหรับการจำลอง ---
    EMPTY = 0
    TREE = 1
    BURNING = 2
    GRID_SIZE = 500
    STEPS = 100

    # ฟังก์ชันสร้างกริดต้นไม้เริ่มต้น
    def initialize_grid(grid_size, tree_density=0.7):
        grid = np.random.choice([EMPTY, TREE], size=(grid_size, grid_size), p=[1 - tree_density, tree_density])
        grid[grid_size // 2, grid_size // 2] = BURNING
        return grid

    # ฟังก์ชันการกระจายไฟ (ปรับให้การแพร่กระจายเน้นไปตามทิศทางลม)
    def spread_fire(grid, slope, wind_direction , burn_prob=0.5, wind_speed=None):
        new_grid = grid.copy()
        wind_bias = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1),
                     'NE': (-1, 1), 'NW': (-1, -1), 'SE': (1, 1), 'SW': (1, -1)}

        # การตั้งค่าเบื้องต้นสำหรับทิศทางลม
        dx, dy = wind_bias.get(wind_direction, (0, 0))

        # การคำนวณการแพร่กระจายของไฟ
        for i in range(1, grid.shape[0] - 1):
            for j in range(1, grid.shape[1] - 1):
                if grid[i, j] == BURNING:
                    new_grid[i, j] = EMPTY  # ไฟที่ไหม้แล้วจะหายไป
                    for di, dj in wind_bias.values():
                        ni, nj = i + di, j + dj
                        if grid[ni, nj] == TREE:
                            # ปรับการลุกลามไฟตามทิศทางลม
                            # เพิ่มความแรงตามทิศทางลม (ตาม wind_direction)
                            wind_effect = wind_speed if (di == dx and dj == dy) else wind_speed / 4
                            slope_factor = 1 + (slope[ni, nj] / 30)
                            wind_factor = 1 + (wind_effect / 10)
                            probability = burn_prob * slope_factor * wind_factor
                            if np.random.random() < probability:
                                new_grid[ni, nj] = BURNING  # ต้นไม้กลายเป็นไฟ
        return new_grid

    def simulate_fire(grid, slope, steps, wind_direction, burn_prob, wind_speed):
        grids = [grid]
        for _ in range(steps):
            grid = spread_fire(grid, slope, wind_direction, burn_prob, wind_speed)
            grids.append(grid)
        return grids

    # --- เริ่มการจำลอง ---
    initial_grid = initialize_grid(GRID_SIZE, tree_density=0.8)
    grids = simulate_fire(initial_grid, terrain_slope, STEPS, wind_direction, burn_prob=0.6, wind_speed=wind_speed)

    # --- สร้างและแสดงวิดีโอ ---
    def create_video(grids, filename="fire_simulation.mp4"):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.axis('off')

        def update(frame):
            ax.clear()
            ax.imshow(grids[frame], cmap='hot', interpolation='nearest')
            ax.set_title(f"Step {frame}")
            ax.axis('off')

        ani = FuncAnimation(fig, update, frames=len(grids), interval=200)
        writer = FFMpegWriter(fps=1)
        ani.save(filename, writer=writer)
        return filename

    video_file = create_video(grids)

    # --- แสดงวิดีโอ ---
    st.video(video_file)

else:
    
    st.write("Please upload an image file to start the simulation.")

