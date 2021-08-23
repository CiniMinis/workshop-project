function stretch_sidebar() {
    console.log(1);
    let window_height = $(window).height();
    let content_offset = $("#contentContainer").offset().top;
    let content_height = $("#contentContainer").height()
    console.log(window_height, content_offset, content_height)
    $("#sidebar").height(Math.max(window_height - content_offset, content_height));
}

$().ready(()=>{
    // Script to make sidebar fill window height 
    // initial fit
    // stretch_sidebar();
    // window change
    // window.onresize = stretch_sidebar;
    // content addition
    // new ResizeObserver(stretch_sidebar).observe(contentContainer);
    // expansion in sidebar
    // $("#sidebarSearchSettingsToggler").click(stretch_sidebar);

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
                <h3 class="bi bi-clock-history ms-auto me-2"></h3>
            </a>
        `);
    }
    // stretch_sidebar();  // stretch to fit new users

    draw_all_avatars();
});
