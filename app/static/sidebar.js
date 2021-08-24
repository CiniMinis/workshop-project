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
                <h3 class="bi bi-clock-history ms-auto me-2"></h3>
            </a>
        `);
    }

    draw_all_avatars();
});
