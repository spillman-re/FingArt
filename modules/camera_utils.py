import cv2

def get_available_cameras():
    available_indices = []
    # Probamos los primeros 5 índices por si acaso
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # CAP_DSHOW es más rápido en Windows
        if cap.isOpened():
            available_indices.append(i)
            cap.release()
    return available_indices