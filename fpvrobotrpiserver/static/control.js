const ARD1_REQEST_INTERVAL = 1000;
const MOTOR_SPEED_MIN = 70;
const MOTOR_SPEED_MAX = 255;
const MOTOR_SPEED_INC = 5;
const CAM_SERVO_POS_BASE = 1000;
const LOW_VOLTAGE = 9.0;

const wsAddr = (document.location.href + 'ws').replace(/^http/, 'ws');
const socket = new WebSocket(wsAddr);

var motorSpeed = MOTOR_SPEED_MIN;

var ard1Request = {
    "motor_l": 0,
    "motor_r": 0,
    "cam_servo_h": 0,
    "cam_servo_v": 0,
    "lighting": 0,
};
var touchIntervals = {};

function sendArd1Request() {
    socket.send(JSON.stringify(ard1Request));
}

function sendCamRequest() {
    var size = $("#resolution").val().split("x"),
        data = {
	"enabled": Boolean(parseInt($("#enable-camera").val())),
	"res_x": parseInt(size[0]),
	"res_y": parseInt(size[1]),
	"quality": parseInt($("#quality").val()),
    };
    $.post('/camera', JSON.stringify(data));
}

function motorSpeedUp() {
    motorSpeed = Math.min(motorSpeed + MOTOR_SPEED_INC, MOTOR_SPEED_MAX);
}

function motorSpeedMin() {
    motorSpeed = MOTOR_SPEED_MIN;
}

function onKeyEvent(eventName, event) {
    var isDown = eventName == "keydown";

    if (event.code == "KeyW") {
	ard1Request["motor_l"] = isDown ? motorSpeed : 0;
	ard1Request["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyS") {
	ard1Request["motor_l"] = isDown ? -motorSpeed : 0;
	ard1Request["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyA") {
	ard1Request["motor_l"] = isDown ? -motorSpeed : 0;
	ard1Request["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyD") {
	ard1Request["motor_l"] = isDown ? motorSpeed : 0;
	ard1Request["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "ArrowLeft") {
	ard1Request["cam_servo_h"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowRight") {
	ard1Request["cam_servo_h"] = isDown ? -1 : 0;
    } else if (event.code == "ArrowDown") {
	ard1Request["cam_servo_v"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowUp") {
	ard1Request["cam_servo_v"] = isDown ? -1 : 0;
    } else if (event.code == "KeyL") {
        if (!isDown)
	    ard1Request["lighting"] = (ard1Request["lighting"] + 1) % 2;
    } else if (event.code == "Home") {
	ard1Request["cam_servo_h"] = CAM_SERVO_POS_BASE + 90;
	ard1Request["cam_servo_v"] = CAM_SERVO_POS_BASE + 90;
    } else if (event.code == "Space") {
	ard1Request["motor_l"] = 0;
	ard1Request["motor_r"] = 0;
	ard1Request["cam_servo_h"] = 0;
	ard1Request["cam_servo_v"] = 0;
	for (const [k, v] of Object.entries(touchIntervals)) {
	    clearInterval(v);
	}
    }
    sendArd1Request();
    $("button[data-code=" + event.code + "]").toggleClass("down", isDown);
}

function onButtonMouseDown() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keydown", event);
    touchIntervals[event.code] = setInterval(onKeyEvent, 50, "keydown", event);
}

function onButtonMouseUp() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keyup", event);
    clearInterval(touchIntervals[event.code]);
}

function onButtonTouchStart(e) {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keydown", event);
    e.preventDefault();
    touchIntervals[event.code] = setInterval(onKeyEvent, 50, "keydown", event);
}

function onButtonTouchEnd(e) {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keyup", event);
    e.preventDefault();
    clearInterval(touchIntervals[event.code]);
}

function onWSMessage(event) {
    var resp = JSON.parse(event.data);
    var v = Math.ceil(resp["voltage"] / 100) / 10;
    $("#voltage").text(v).toggleClass("low", v < LOW_VOLTAGE);
}


setInterval(sendArd1Request, ARD1_REQEST_INTERVAL);
socket.addEventListener('message', onWSMessage);

document.addEventListener("keydown", (event) => {
    onKeyEvent("keydown", event);
});
document.addEventListener("keyup", (event) => {
    onKeyEvent("keyup", event);
});

$(document).ready(function($) {
    $("#button-box button")
	.on("mousedown", onButtonMouseDown)
	.on("mouseup", onButtonMouseUp)
	.on("touchstart", onButtonTouchStart)
	.on("touchend", onButtonTouchEnd);
    $("#camera-params-icon").click(function () {
	$("#camera-params").fadeToggle();
    });
    $("#enable-camera").change(sendCamRequest);
    $("#resolution").change(function () {
	var $body = $("body");
	$("#resolution option").each(function() {
	    $body.removeClass("res" + $(this).val());
	});
	sendCamRequest();
	$body.addClass("res" + $(this).val());
    });
    $("#quality").change(sendCamRequest);
    $("#voltage-box").click(function() {
	if (window.confirm("Power off?")) {
	    $.post('/power-off', JSON.stringify({}));
	}
    });
});
