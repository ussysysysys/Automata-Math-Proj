import matplotlib.pyplot as plt

# สร้างกราฟตัวอย่าง
x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

plt.plot(x, y, label='Example Plot')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Test Plot')
plt.legend()
plt.show()
