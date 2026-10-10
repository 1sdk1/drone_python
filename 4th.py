import pyhula
import time
import math

#API読み込みコピペ
api = pyhula.UserApi()
if not api.connect():
    print("connect error")
else:
    print("connection to station by wifi")

print(f"battery={api.get_battery()}")

#相対位置をカメラ基準からドローン基準に直す関数
def camera_to_drone(camera_relative_x,camera_relative_y,camera_relative_z,camera_angle):
    drone_relative_x = camera_relative_x
    drone_relative_y = camera_relative_y*math.cos(math.radians(camera_angle)) + camera_relative_z*math.sin(math.radians(camera_angle))
    drone_relative_z = camera_relative_z*math.cos(math.radians(camera_angle)) - camera_relative_y*math.sin(math.radians(camera_angle))
    return drone_relative_x, drone_relative_y, drone_relative_z

#QRコードに近づく関数
def qr_get_closer(relative_x,relative_y,scale):
    if relative_x > 0 :
        api.single_fly_right(int(relative_x*scale))
    if relative_x < 0 :
        api.single_fly_left(int(abs(relative_x)*scale))

    if relative_y > 0 :
        api.single_fly_forward(int(relative_y*scale))
    if relative_y < 0 :
        api.single_fly_back(int(abs(relative_y)*scale))

#QRを読み取ってから近づく関数
def auto_get_closer(scale):
    array = api.single_fly_Anticipatory_recognition(0)
    if array["result"]:
        relative_x, relative_y, relative_z = camera_to_drone(array["x"],array["y"],array["z"],camera_angle)
        
        if abs(relative_x) < 10 and abs(relative_y) < 10:
            print("既に十分近い位置にいます")
            return {"result":array["result"], 
            "relative_x":relative_x, 
            "relative_y":relative_y, 
            "relative_z":relative_z}
        else:
            print(f"ドローン基準でQRの相対位置({relative_x:.2f},{relative_y:.2f},{relative_z:.2f})に近づきます")
            qr_get_closer(relative_x,relative_y,scale)
            return {"result":array["result"], 
            "relative_x":relative_x, 
            "relative_y":relative_y, 
            "relative_z":relative_z}

    else:
        print("QR NOT FOUND")
        return {"result":array["result"]}

# 右　前　上　が　それぞれ x　y　z　の正

# ストリームを有効化
api.Plane_cmd_swith_rtp(0)
api.single_fly_flip_rtp()
print("映像取得開始...")

#カメラの角度設定 camera_angleは水平方向から下向きに何度か
camera_angle = 60
api.Plane_cmd_camera_angle(1,camera_angle)

# SPS/PPSが届くまで待機
time.sleep(3)

#QRを見つけた時のFlagを初期化
qr_flag = 0

#離陸
api.single_fly_takeoff()

#探索処理
while  True:

    while True:
            
        array = api.single_fly_Anticipatory_recognition(0)
        
        if array["result"]:
            print("QR発見")
            qr_flag = 1
            break

        if qr_flag == 1:
            time.sleep(2)
            api.single_fly_back(40)
            camera_angle = 50
            api.Plane_cmd_camera_angle(1,camera_angle)
            print("見失ったから後進")
            array = api.single_fly_Anticipatory_recognition(0)
            if array["result"]:
                print("再発見")
                qr_flag = 0

        else: 
            api.single_fly_forward(20)
            print("QRないから前進")

    relative_x, relative_y, relative_z = camera_to_drone(array["x"],array["y"],array["z"],camera_angle)
    print(f"ドローン基準でのQRの相対位置(x,y,z): {relative_x:.2f}, {relative_y:.2f}, {relative_z:.2f}")

    if 0 < abs(relative_x) < 40 and 0 < abs(relative_y) < 40:
        camera_angle = 90
        api.Plane_cmd_camera_angle(1,camera_angle)
        auto_get_closer(1)
        api.single_fly_touchdown()

    # qr_get_closer(relative_x,relative_y,0.2)
    # array = api.single_fly_Anticipatory_recognition(0)

    # while True:
    #     if array["result"]:
    #         print("接近中")
    #         auto_get_closer(0.2)
    #     else:
    #         break
    else:
        qr_get_closer(relative_x,relative_y,0.9)
        print("接近したので真下を向く")
        camera_angle = 90
        api.Plane_cmd_camera_angle(1,camera_angle)
        api.single_fly_up(25)

        auto_closer_return = auto_get_closer(0.9)

        if auto_closer_return["result"]:
            auto_closer_return = auto_get_closer(0.9)
            api.single_fly_touchdown()
            break


        
    







 





















