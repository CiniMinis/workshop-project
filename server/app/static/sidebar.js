$().ready(()=>{

    // configure buttons
    bind_button_to_collapse("sidebarSearchSettingsToggler", "sidebarSearchSettings");

    // add the recently viewed users to the sidebar
    let recent_users = get_recent_users();
    for (let i = 0; i < recent_users.length; i++) {
        [user_id, user_name] = recent_users[i];
        $("#sidebarRecentUsers").append(`
            <a href="/user/${user_id}" class="recent_user container d-flex justify-content-start align-items-center p-2 m-2 white-box rounded">
                <canvas class="avatar avatar-side rounded light-box me-2" data-user-id='${user_id}'></canvas>
                ${user_name}
                <h3 class="bi bi-clock-history ms-auto align-self-start"></h3>
            </a>
        `);
    }

    draw_all_avatars();
});

$(window).scroll(function() {
    toggle_top_button_margin = 100;
    animation_len = 500;
    console.log($(window).scrollTop());
    console.log($("#scrollTopBtn").data("visible"));
    // check if bottom of page is reached
    if ($(window).scrollTop() > toggle_top_button_margin && ! $("#scrollTopBtn").data("visible")) {
        $("#scrollTopBtn").data("visible", true);
        $("#scrollTopBtn").animate({ "opacity": "1" }, animation_len);
    } else if ($(window).scrollTop() < toggle_top_button_margin && $("#scrollTopBtn").data("visible")) {
        $("#scrollTopBtn").data("visible", false);
        $("#scrollTopBtn").animate({ "opacity": "0" }, animation_len);
    }
});
