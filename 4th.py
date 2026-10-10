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

#移動スピード(cm/s)
moving_speed = 50

#相対位置をカメラ基準からドローン基準に直す関数
def camera_to_drone(camera_relative_x,camera_relative_y,camera_relative_z,camera_angle):
    drone_relative_x = camera_relative_x
    drone_relative_y = camera_relative_y*math.cos(math.radians(camera_angle)) + camera_relative_z*math.sin(math.radians(camera_angle))
    drone_relative_z = camera_relative_z*math.cos(math.radians(camera_angle)) - camera_relative_y*math.sin(math.radians(camera_angle))
    return drone_relative_x, drone_relative_y, drone_relative_z

#QRコードに近づく関数
def qr_get_closer(relative_x,relative_y,scale):
    if relative_x > 0 :
        api.single_fly_right(int(relative_x*scale),moving_speed)
    if relative_x < 0 :
        api.single_fly_left(int(abs(relative_x)*scale),moving_speed)

    if relative_y > 0 :
        api.single_fly_forward(int(relative_y*scale),moving_speed)
    if relative_y < 0 :
        api.single_fly_back(int(abs(relative_y)*scale),moving_speed)

#QRを読み取ってから近づく関数で、返ってくるQRの相対位置は移動後のもの
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
            array = api.single_fly_Anticipatory_recognition(0)
            relative_x, relative_y, relative_z = camera_to_drone(array["x"],array["y"],array["z"],camera_angle)

            return {"result":array["result"], 
            "relative_x":relative_x, 
            "relative_y":relative_y, 
            "relative_z":relative_z}
    else:
        print("QR NOT FOUND")
        return {"result":array["result"]}

# 右　前　上　がそれぞれ　x　y　z　の正

# ストリームを有効化
api.Plane_cmd_swith_rtp(0)
api.single_fly_flip_rtp()
print("映像取得開始...")

#カメラの角度設定 camera_angleは水平方向から下向きに何度か
camera_angle = 60
api.Plane_cmd_camera_angle(1,camera_angle)

# SPS/PPSが届くまで待機
time.sleep(3)

#初期化
qr_flag = 0
back_count = 0
process_finished = False
low_height = False

#離陸
api.single_fly_takeoff()

#探索処理
while  True:
    while True:

        #QRが見つかった場合
        array = api.single_fly_Anticipatory_recognition(0)
        if array["result"]:
            print("QR発見")
            qr_flag = 1
            break

        #一度発見したのに見失った場合は最大n回まで下がる
        if qr_flag == 1:
            while back_count < 2:
                back_count += 1
                print("見失ったから後進")
                api.single_fly_back(40)
                camera_angle = 60
                api.Plane_cmd_camera_angle(1,camera_angle)
                array = api.single_fly_Anticipatory_recognition(0)
                if array["result"]:
                    print("再発見")
                    back_count = 0
                    break
            else:
                print("後進したが見つからないのでリセット")
                print(array)
                back_count = 0
                qr_flag = 0
                continue
            break

        #まだ一度も見つけていなくて発見できない場合はただ前進
        else: 
            api.single_fly_forward(20)
            print("QRないから前進")

    #QRに向かって行って下を向く
    relative_x, relative_y, relative_z = camera_to_drone(array["x"],array["y"],array["z"],camera_angle)
    print(f"ドローン基準でのQRの相対位置(x,y,z): {relative_x:.2f}, {relative_y:.2f}, {relative_z:.2f}")
    qr_get_closer(relative_x,relative_y,0.9)
    print("接近したから真下を向く")
    camera_angle = 90
    api.Plane_cmd_camera_angle(1,camera_angle)
    time.sleep(1)
    api.single_fly_up(20)

    while True:
        auto_closer_return = auto_get_closer(1)
        print(auto_closer_return)

        if auto_closer_return["result"]:

            if abs(auto_closer_return["relative_x"]) < 10 and abs(auto_closer_return["relative_y"]) < 10:
                print("真上なので着地します")
                api.single_fly_touchdown()
                process_finished = True
                break

            if abs(auto_closer_return["relative_x"]) < 30 and abs(auto_closer_return["relative_y"]) < 30:
                print("近いので高度を下げます")
                api.single_fly_down(35)
                low_height = True

        else:
            print("見逃した")
            if low_height == True:
                low_height = False
                api.single_fly_up(15)
            else:
                api.single_fly_down(20)
            break

    if process_finished == True:
        print("処理Finished!")
        break










 





















