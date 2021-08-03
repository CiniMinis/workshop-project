function fetch_part_from_dna(dna, part) {
    return new Promise((resolve, reject) => {
        var request = $.ajax({
            url: '/api/part_from_dna',
            type: 'POST',
            data: {
                'part': part,
                'dna': dna
            }
        });
        request.done((result) => {
            // console.log(result)
            if (result['status'] === 'success'){
                resolve(result['content'])
            }
            reject(result['content'])
        });
    });
}

function draw_dna(){
    var dna = $('#dnaToDraw').val();
    var drawCanvas = $('#drawDNACanvas')[0];
    var ctx = drawCanvas.getContext('2d');
    var json_parts = AVATAR_BODY_PARTS.map(fetch_part_from_dna.bind(undefined, dna));
    last_promise = clearCanvas(drawCanvas);
    for (let i = 0; i < json_parts.length; i++) {
        last_promise = Promise.all([json_parts[i], last_promise])
            .then((vals) => {
                console.log(vals);
                return draw_json_part(ctx, vals[0]);
            });
    }
    last_promise.catch((err) => {console.log(err);});
}