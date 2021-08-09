const AVATAR_WIDTH = 500;
const AVATAR_HEIGHT = AVATAR_WIDTH;
const AVATAR_BODY_PARTS = ["body", "ears", "head", "mouth", "eyes", "nose"];
const PRIVATE_AVATAR = "/img/avatar/private.svg";
const USER_ID_ATTR = "data-user-id";
const WAS_DRAWN_NAME = "was-drawn";

function fetch_image(src) {
    return new Promise((resolve) => {
        var img = new Image();
        img.onload = () => resolve(img);
        img.src = src;
    });
}

function recolor_image(new_color, img) {
    // create canvas on which the new image is generated
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = AVATAR_WIDTH;
    canvas.height = AVATAR_HEIGHT;

    // draw the image to color
    ctx.drawImage(img, 0, 0);

    // override the canvas color with new color
    ctx.globalCompositeOperation = "source-in";
    ctx.fillStyle = new_color;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // return a new image promise for the recolored image
    return canvas;
}

function draw_promise(context, img) {
    return new Promise((resolve) => {
        context.drawImage(img, 0, 0);
        resolve();
    });
}

function draw_json_part(context, json) {
    return new Promise((resolve) => {
        // variable for promises to which we wait
        let promises = []
        // draw the body part
        promises.push(
            fetch_image(json['border_image'])
                .then(draw_promise.bind(undefined, context))
        );
        
        if (!!json['color_image']) {
            promises.push(
                fetch_image(json['color_image']['image'])
                    .then(recolor_image.bind(undefined, json['color_image']['rgb']))
                    .then(draw_promise.bind(undefined, context))
            );
        }
        
        Promise.allSettled(promises).then(resolve);
    });
}


// draws private user image
function draw_private_avatar(context) {
    return new Promise((resolve) => {
        fetch_image(PRIVATE_AVATAR)
            .then(draw_promise.bind(undefined, context))
            .then(resolve);
    });
}

// clears the canvas
function clearCanvas(canvas) {
    return new Promise(resolve => {
        const ctx = canvas.getContext("2d");

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        resolve();
    });
}

// fetches body part from user id
function fetch_part_from_user(user_id, part) {
    return new Promise((resolve, reject) => {
        var request = $.ajax({
            url: '/api/part_from_user',
            type: 'POST',
            data: {
                'id': user_id,
                'part': part
            }
        });
        request.done((result) => {
            if (result['status'] === 'success'){
                resolve(result['content'])
            }
            reject(result['content'])
        });
    });
}

function canvas_from_json(part_json) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = AVATAR_WIDTH;
        canvas.height = AVATAR_HEIGHT;
        const ctx = canvas.getContext('2d');
        draw_json_part(ctx, part_json)
            .then(() => {
                resolve(canvas);
            });
    });
}

function draw_user(canvas, user_id){
    var ctx = canvas.getContext('2d');
    var json_parts = AVATAR_BODY_PARTS.map(fetch_part_from_user.bind(undefined, user_id));
    var promises = [];
    for (let i = 0; i < json_parts.length; i++) {
        promises.push(json_parts[i].then(canvas_from_json));
    }
    Promise.all(promises)
        .then((body_parts) => {
            body_parts.forEach((part) => {
                ctx.drawImage(part, 0, 0);
            });
        })
        .catch((err) => {draw_private_avatar(ctx)});
}

function prepare_avatar(avatar) {
    // dont redraw drawn canvases
    if ($(avatar).data(WAS_DRAWN_NAME))
        return;
    
    $(avatar).data(WAS_DRAWN_NAME, true);

    // initialize basic avatar properties
    avatar.width = AVATAR_WIDTH;
    avatar.height = AVATAR_HEIGHT;

    // if avatar is bound to a user id, draw it
    if (!avatar.hasAttribute(USER_ID_ATTR))
        return;
    user_id = avatar.getAttribute(USER_ID_ATTR);
    draw_user(avatar, user_id);
}

function draw_all_avatars(){
    $(".avatar").map((i, avatar) => {prepare_avatar(avatar)});
}

$().ready(draw_all_avatars);


function bind_button_to_collapse(button_id, collapsable_id, extend_icon="bi-plus-lg", retract_icon="bi-dash-lg") {
    // make icon show retraction when extended
    $(`#${collapsable_id}`).on('show.bs.collapse', () => {
        $(`#${button_id} > i`).addClass(retract_icon).removeClass(extend_icon);
    });

    // make icon show extention when retracted
    $(`#${collapsable_id}`).on('hide.bs.collapse', () => {
        $(`#${button_id} > i`).addClass(extend_icon).removeClass(retract_icon);
    });

    // set current icon to match starting state
    if ($(`#${collapsable_id}`).attr("aria-expanded")) {
        $(`#${button_id} > i`).addClass(retract_icon).removeClass(extend_icon);
    } else {
        $(`#${button_id} > i`).addClass(extend_icon).removeClass(retract_icon);
    }
}