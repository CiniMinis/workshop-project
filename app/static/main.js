const AVATAR_WIDTH = 500;
const AVATAR_HEIGHT = AVATAR_WIDTH;
const AVATAR_BODY_PARTS = ["body", "ears", "head", "mouth", "eyes", "nose"];
const PRIVATE_AVATAR = "/img/avatar/private.svg";

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
    return fetch_image(canvas.toDataURL("image/png"));
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

function draw_user(canvas, user_id){
    var ctx = canvas.getContext('2d');
    var json_parts = AVATAR_BODY_PARTS.map(fetch_part_from_user.bind(undefined, user_id));
    last_promise = clearCanvas(canvas);
    for (let i = 0; i < json_parts.length; i++) {
        last_promise = Promise.all([json_parts[i], last_promise])
            .then((vals) => {
                return draw_json_part(ctx, vals[0]);
            });
    }
    last_promise.catch((err) => {draw_private_avatar(ctx)});
}


$().ready(() => {
    // set avatars to correct size
    $(".avatar")
        .each((i, avatar) => {
            avatar.width = AVATAR_WIDTH;
            avatar.height = AVATAR_HEIGHT;
        }).filter("[data-user-id]")
        .each((i, avatar) => {
            user_id = avatar.getAttribute("data-user-id");
            draw_user(avatar, user_id)
        });
});
