const AVATAR_WIDTH = 500;
const AVATAR_HEIGHT = AVATAR_WIDTH;

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

function generate_body_part(body_part, type, color = null) {
    return new Promise((resolve) => {
        // Temporary, Drawing on test canvas
        const canvas = document.getElementById("TestCanvas");
        const ctx = canvas.getContext("2d");

        // interior is colored, border doesn't change
        let part_interior = `/img/avatar/${body_part}/color${type}.png`;
        let part_border = `/img/avatar/${body_part}/border${type}.png`;

        // variable for promises to which we wait
        let promises = []

        // draw the body part
        promises.push(
            fetch_image(part_border)
                .then(draw_promise.bind(undefined, ctx))
        );

        if (color) {
            promises.push(
                fetch_image(part_interior)
                    .then(recolor_image.bind(undefined, color))
                    .then(draw_promise.bind(undefined, ctx))
            );
        }

        Promise.allSettled(promises).then(resolve);
    });
}

// random int from start with amount possibilities
function randInt(amount, start = 1) {
    return start + Math.floor(Math.random() * amount);
}

// randomly selects an RGB color
function randomColor() {
    return "#" + randInt(2 ** 24, 0).toString(16);
}

// clears the canvas
function clearCanvas() {
    return new Promise(resolve => {
        // Temporary, Drawing on test canvas
        const canvas = document.getElementById("TestCanvas");
        const ctx = canvas.getContext("2d");

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        resolve();
    });
}

// randomly set a face
function randomizeFace() {
    clearCanvas()
        .then(() => { return generate_body_part("body", "1", randomColor()) })
        .then(() => { return generate_body_part("ears", randInt(2), randomColor()) })
        .then(() => { return generate_body_part("head", randInt(4), randomColor()) })
        .then(() => { return generate_body_part("eyes", randInt(4), randomColor()) })
        .then(() => { return generate_body_part("mouth", randInt(4), randomColor()) })
        .then(() => { return generate_body_part("nose", randInt(2)) });
}

$().ready(() => {
    // set avatars to correct size
    $(".avatar").each((i, avatar) => {
        avatar.width = AVATAR_WIDTH;
        avatar.height = AVATAR_HEIGHT;
    });
});
