const MOTOR_SPEED_MIN = 70;
const MOTOR_SPEED_MAX = 255;
const MOTOR_SPEED_INC = 5;

const LOW_VOLTAGE = 9.0;

const wsAddr = (document.location.href + 'ws').replace(/^http/, 'ws');
const socket = new WebSocket(wsAddr);

var motorSpeed = MOTOR_SPEED_MIN;

var ard0Request = {
    "type": "ard0",
    "motor_l": 0,
    "motor_r": 0,
    "cam_servo_h": 0,
    "cam_servo_v": 0,
    "lighting": 0,
};

function sendArd0Request() {
    socket.send(JSON.stringify(ard0Request));
}

function sendCamRequest() {
    var size = $("#resolution").val().split("x"),
        data = {
	"res_x": parseInt(size[0]),
	"res_y": parseInt(size[1]),
	"quality": parseInt($("#quality").val()),
    };
    $.post('/camera-params', JSON.stringify(data));
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
	ard0Request["motor_l"] = isDown ? motorSpeed : 0;
	ard0Request["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyS") {
	ard0Request["motor_l"] = isDown ? -motorSpeed : 0;
	ard0Request["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyA") {
	ard0Request["motor_l"] = isDown ? -motorSpeed : 0;
	ard0Request["motor_r"] = isDown ? motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "KeyD") {
	ard0Request["motor_l"] = isDown ? motorSpeed : 0;
	ard0Request["motor_r"] = isDown ? -motorSpeed : 0;
        if (isDown) {motorSpeedUp();} else {motorSpeedMin();}
    } else if (event.code == "ArrowLeft") {
	ard0Request["cam_servo_h"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowRight") {
	ard0Request["cam_servo_h"] = isDown ? -1 : 0;
    } else if (event.code == "ArrowDown") {
	ard0Request["cam_servo_v"] = isDown ? 1 : 0;
    } else if (event.code == "ArrowUp") {
	ard0Request["cam_servo_v"] = isDown ? -1 : 0;
    } else if (event.code == "KeyL") {
        if (!isDown)
	    ard0Request["lighting"] = (ard0Request["lighting"] + 1) % 2;
    } else if (event.code == "Home") {
	ard0Request["cam_servo_h"] = 1090;
	ard0Request["cam_servo_v"] = 1090;
    } else if (event.code == "Space") {
	ard0Request["motor_l"] = 0;
	ard0Request["motor_r"] = 0;
	ard0Request["cam_servo_h"] = 0;
	ard0Request["cam_servo_v"] = 0;
    }
    sendArd0Request();
    $("button[data-code=" + event.code + "]").toggleClass("down", isDown);
}

function onButtonMouseDown() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keydown", event);
}

function onButtonMouseUp() {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keyup", event);
}

function onButtonTouchStart(e) {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keydown", event);
    e.preventDefault();
}

function onButtonTouchEnd(e) {
    var event = {
	code: $(this).attr("data-code"),
    };
    onKeyEvent("keyup", event);
    e.preventDefault();
}

function onWSMessage(event) {
    var resp = JSON.parse(event.data);
    if (resp.type == "ard0") {
	var v = Math.ceil(resp["voltage"] / 100) / 10;
	$("#voltage").text(v);
	if (v <= LOW_VOLTAGE) {
	    $("#voltage-symbol").html("&#x1faab;");
	} else {
	    $("#voltage-symbol").html("&#x1f50b;");
	}
    }
}


setInterval(sendArd0Request, 1000);
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
	$("#camera-params-table").fadeToggle();
    });
    $("#resolution").change(function () {
	var $body = $("body");
	$("#resolution option").each(function() {
	    $body.removeClass("res" + $(this).val());
	});
	sendCamRequest();
	$body.addClass("res" + $(this).val());
    });
    $("#quality").change(sendCamRequest);
});
