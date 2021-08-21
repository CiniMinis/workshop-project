function stretch_sidebar() {
    let window_height = $(window).height();
    let content_offset = $("#contentContainer").offset().top;
    let content_height = $("#contentContainer").height()
    $("#sidebar").height(Math.max(window_height - content_offset, content_height));
}

$().ready(()=>{
    // Script to make sidebar fill window height 
    // initial fit
    stretch_sidebar();
    // window change
    window.onresize = stretch_sidebar;
    // content addition
    new ResizeObserver(stretch_sidebar).observe(contentContainer);

    // configure buttons
    bind_button_to_collapse("sidebarSearchSettingsToggler", "sidebarSearchSettings");

    // add the recently viewed users to the sidebar
    let recent_users = get_recent_users();
    for (let i = 0; i < recent_users.length; i++) {
        [user_id, user_name] = recent_users[i];
        $("#sidebarRecentUsers").append(`
            <canvas class="avatar avatar-small border border-primary" data-user-id='${user_id}'></canvas>
            <a href="/user/${user_id}">${user_name}</a>
            <br/>
        `);
    }
    draw_all_avatars();
});
