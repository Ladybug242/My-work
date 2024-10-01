import random
import cv2
import websockets
import asyncio
import logging
from abc import ABC, abstractmethod
import jwt
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Создание ключей для прокси
SECRET_KEY_PART_1 = "secret_"
SECRET_KEY_PART_2 = "key"

def get_secret_key():
    return SECRET_KEY_PART_1 + SECRET_KEY_PART_2

# паттерн Декоратор
class IDrone(ABC):
    @abstractmethod
    def move_to(self, coord):
        pass

    @abstractmethod
    def takeoff(self):
        pass

    @abstractmethod
    def land(self):
        pass

# Создание объекта
class Drone(IDrone):
    def move_to(self, coord):
        logging.info(f"Дрон летит к {coord}")

    def takeoff(self):
        logging.info("Дрон взлетает")

    def land(self):
        logging.info("Дрон приземляется")

# Паттерн Proxy и Secure Proxy
class DroneSecureProxy(IDrone):
    def __init__(self, drone: Drone, control_drone):
        self.drone = drone
        # Инициализация прокси с функцией управления дроном
        self.control_drone = control_drone

    def set_secret_key(self, secret_key):
        self.secret_key = secret_key

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload["user_id"]
        except jwt.ExpiredSignatureError as e:
            print(f"Истек токен: {e}")
            return
        except jwt.InvalidTokenError as e:
            print(f"Токен не валиден: {e}")

    def move_to(self, coord, token):
        user_id = self.verify_token(token)
        if user_id:
            logging.info(f"Прокси: перехвачен вызов от user:{user_id} к move_to")
            self.drone.move_to(coord)

    def takeoff(self, token):
        user_id = self.verify_token(token)
        if user_id:
            logging.info(f"Прокси: перехвачен вызов от user:{user_id} к takeoff")
            self.drone.takeoff()

    def land(self, token):
        user_id = self.verify_token(token)
        if user_id:
            logging.info(f"Прокси: перехвачен вызов от user:{user_id} к land")
            self.drone.land()

    async def __call__(self, websocket, path):
        # Обработка входящих сообщений по вебсокету
        async for msg in websocket:
            # Проверка авторизации
            if self.is_auth(websocket):
                # Если авторизация прошла, передаем управление дроном
                await self.control_drone(websocket, path, msg)
            else:
                # Если авторизация не прошла, отправляем сообщение об ошибке
                await websocket.send("Неавторизированный доступ")

    def is_auth(self, websocket):
        try:
            # Проверка наличия параметров в пути вебсокета
            if "?" in websocket.path:
                params = websocket.path.split("?")[1]
                # Обработка параметров, разделенных амперсандом, и проверка наличия "="
                params = dict(param.split("=") for param in params.split("&") if "=" in param)
                # Проверка токена на валидность
                return params.get("token") == "valid_token"
        except Exception as e:
            # Логирование ошибки аутентификации
            logging.info(f"Ошибка аутентификации: {e}")
        return False

async def control_drone(websocket, path, msg):
    try:
        # Логирование полученной команды
        logging.info(f"Получена команда: {msg}")
        # print(f"Получена команда: {msg}") # Закомментировано для логирования
        if msg == "takeoff":
            # Логирование и отправка команды взлета
            logging.info(f"Дрон взлетает")
            await websocket.send("Дрон взлетает")
        elif msg == "land":
            # Логирование и отправка команды приземления
            logging.info(f"Дрон приземляется")
            await websocket.send("Дрон приземляется")
        elif msg == "accu":
            # Логирование и отправка команды приземления
            logging.info(f"Проверка зарядки")
            await websocket.send(f"Заряд аккумулятора {random.randint(70,90)} %")
        elif msg == "high_flight":
            # Логирование и отправка команды приземления
            logging.info(f"Высота полета")
            await websocket.send(f"Высота полета {random.randint(100,250)} м")
        elif msg == "take_photo":
            # Логирование и отправка команды приземления
            logging.info(f"Фотосъемка")
            # Загрузка изображения с камеры БПЛА
            cam = cv2.VideoCapture(0)
            answer, image = cam.read()
            cv2.imwrite('ph.jpg', image)
            # Проверка, что изображение загружено
            if answer is None:
                raise ValueError("Не удалось загрузить изображение. Проверьте доступность камеры.")
            await websocket.send(f"Фото сохранено")

    except websockets.ConnectionClosed as e:
        # Логирование закрытия соединения
        logging.info(f"Соединение закрыто: {e}")
    except Exception as e:
        # Логирование прочих исключений
        logging.info(e)

def generate_token(user_id):
    expiration_time = datetime.utcnow() + timedelta(seconds=5)
    token = jwt.encode({"user_id": user_id, "exp": expiration_time}, get_secret_key(), algorithm="HS256")
    return token


async def main():
    # Создание экземпляра прокси
    proxy = DroneSecureProxy(drone, control_drone)
    # Запуск вебсокет-сервера
    async with websockets.serve(proxy, host="localhost", port=5005) as server:
        try:
            # Ожидание закрытия сервера
            await server.wait_closed()
        except Exception as e:
            # Логирование ошибок при работе сервера
            logging.info(e)
            logging.info("Сервер закрыт")


if __name__ == '__main__':

    user_id = "operator"
    token = generate_token(user_id)
    logging.info(f"User {user_id} получил токен: {token}")
    # Дрон
    drone = Drone()
    drone_proxy = DroneSecureProxy(drone, control_drone)
    drone_proxy.set_secret_key(get_secret_key())

    drone_proxy.takeoff(token)
    drone_proxy.move_to((34.5555, 25.4444, 500), token)

    import time

    time.sleep(6)
    drone_proxy.land(token)

    #Запуск главной асинхронной функции
    asyncio.run(main())