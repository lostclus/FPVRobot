const DEVICE_MOTOR_L = 1;
const DEVICE_MOTOR_R = 2;
const DEVICE_CAM_SERVO_H = 3;
const DEVICE_CAM_SERVO_V = 4;
const DEVICE_CAM_SERVO_MOVE_H = 5;
const DEVICE_CAM_SERVO_MOVE_V = 6;
const DEVICE_VOLAGE = 7;

const wsAddr = (document.location.href + 'ws').replace(/^http/, 'ws');
const socket = new WebSocket(wsAddr);

function sendDevMsg(device, value) {
    var payload = JSON.stringify(
        {
            "type": "device",
            "device": device,
            "value": value,
        },
    );
    socket.send(payload);
}

function sendPing() {
    var payload = JSON.stringify(
        {
            "type": "ping",
        },
    );
    socket.send(payload);
}

function onKeyEvent(eventName, event) {
    var isUp = eventName == "keyup";
    var isDown = eventName == "keydown";

    if (event.code == "KeyW") {
        sendDevMsg(DEVICE_MOTOR_L, isDown ? 100 : 0);
        sendDevMsg(DEVICE_MOTOR_R, isDown ? 100 : 0);
    } else if (event.code == "KeyS") {
        sendDevMsg(DEVICE_MOTOR_L, isDown ? -100 : 0);
        sendDevMsg(DEVICE_MOTOR_R, isDown ? -100 : 0);
    } else if (event.code == "KeyA") {
        sendDevMsg(DEVICE_MOTOR_L, isDown ? 100 : 0);
    } else if (event.code == "KeyD") {
        sendDevMsg(DEVICE_MOTOR_R, isDown ? 100 : 0);
    } else if (event.code == "ArrowLeft") {
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_H, isDown ? 1 : 0);
    } else if (event.code == "ArrowRight") {
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_H, isDown ? -1 : 0);
    } else if (event.code == "ArrowDown") {
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_V, isDown ? 1 : 0);
    } else if (event.code == "ArrowUp") {
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_V, isDown ? -1 : 0);
    } else if (event.code == "Escape") {
        sendDevMsg(DEVICE_MOTOR_L, 0);
        sendDevMsg(DEVICE_MOTOR_R, 0);
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_H, 0);
        sendDevMsg(DEVICE_CAM_SERVO_MOVE_V, 0);
    }
}

setInterval(sendPing, 1000);

document.addEventListener("keydown", (event) => {
    onKeyEvent("keydown", event);
});
document.addEventListener("keyup", (event) => {
    onKeyEvent("keyup", event);
});
