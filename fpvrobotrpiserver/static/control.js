const MOTOR_SPEED_MIN = 70;
const MOTOR_SPEED_MAX = 255;
const MOTOR_SPEED_INC = 5;

const wsAddr = (document.location.href + 'ws').replace(/^http/, 'ws');
const socket = new WebSocket(wsAddr);

var motorSpeed = MOTOR_SPEED_MIN;

var wsRequest = {
    "motor_l": 0,
    "motor_r": 0,
    "cam_servo_h": 0,
    "cam_servo_v": 0,
    "lighting": 0,
};


function sendWSRequest() {
    socket.send(JSON.stringify(wsRequest));
}

function motorSpeedUp() {
    motorSpeed = Math.min(motorSpeed + MOTOR_SPEED_INC, MOTOR_SPEED_MAX);
}

function motorSpeedMin() {
    motorSpeed = MOTOR_SPEED_MIN;
}

function onKeyEvent(eventName, event) {
    var isUp = eventName == "keyup";
    var isDown = eventName == "keydown";

    if (event.code == "KeyW") {
	wsRequest["motor_l"] = isDown ? motorSpeed : 0;
	wsRequest["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyS") {
	wsRequest["motor_l"] = isDown ? -motorSpeed : 0;
	wsRequest["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyA") {
	wsRequest["motor_l"] = isDown ? -motorSpeed : 0;
	wsRequest["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyD") {
	wsRequest["motor_l"] = isDown ? motorSpeed : 0;
	wsRequest["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "ArrowLeft") {
	wsRequest["cam_servo_h"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowRight") {
	wsRequest["cam_servo_h"] = isDown ? -1 : 0;
    } else if (event.code == "ArrowDown") {
	wsRequest["cam_servo_v"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowUp") {
	wsRequest["cam_servo_v"] = isDown ? -1 : 0;
    } else if (event.code == "KeyL") {
        if (isUp)
	    wsRequest["lighting"] = (wsRequest["lighting"] + 1) % 8;
    } else if (event.code == "Home") {
	wsRequest["cam_servo_h"] = 1090;
	wsRequest["cam_servo_v"] = 1090;
    } else if (event.code == "Space") {
	wsRequest["motor_l"] = 0;
	wsRequest["motor_r"] = 0;
	wsRequest["cam_servo_h"] = 0;
	wsRequest["cam_servo_v"] = 0;
    }
    sendWSRequest();
}

function onTouchStart() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keydown", event);
}

function onTouchEnd() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keyup", event);
}

function onWSResponse(event) {
    var response = JSON.parse(event.data);
    $("#voltage").text(
	response["voltage"] / 1000
    );
}


setInterval(sendWSRequest, 1000);

document.addEventListener("keydown", (event) => {
    onKeyEvent("keydown", event);
});
document.addEventListener("keyup", (event) => {
    onKeyEvent("keyup", event);
});

$(document).ready(function($) {
    $("#button-box button")
	.on("touchstart", onTouchStart)
	.on("touchend", onTouchEnd);
});

socket.addEventListener('message', onWSResponse);
