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
            <a href="/user/${user_id}" class="recent_user container d-flex justify-content-start align-items-center p-2 m-2 bg-light border rounded border-dark">
                <canvas class="avatar avatar-side border rounded border-dark me-4" data-user-id='${user_id}'></canvas>
                <h5>${user_name}</h5>
                <h3 class="bi bi-clock-history ms-auto m-4"></h3>
            </a>
        `);
    }
    stretch_sidebar();  // stretch to fit new users

    draw_all_avatars();
});
