function bind_button_to_collapse(button_id, collapsable_id, extend_icon="bi-plus-lg", retract_icon="bi-dash-lg") {
    // make icon show retraction when extended
    $(`#${collapsable_id}`).on('show.bs.collapse', () => {
        $(`#${button_id} > i`).addClass(retract_icon).removeClass(extend_icon);
    });

    // make icon show expansion when retracted
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