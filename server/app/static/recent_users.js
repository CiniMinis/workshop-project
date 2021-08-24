MAX_RECENT_USERS = 3;
RECENT_USERS_KEY = "recentUsers";


function get_recent_users() {
    let user_storage = localStorage.getItem(RECENT_USERS_KEY);
    if (!user_storage)
        return [];
    return JSON.parse(user_storage);
}

function add_user_to_recents(user_id, user_name) {
    let user_storage = get_recent_users();

    // if user in recents, remove it. It will change position
    user_storage = user_storage.filter(user => (user[0] != user_id));

    // add user to start
    user_storage.unshift([user_id, user_name]);

    // remove oldest if overfilled
    if (user_storage.length > MAX_RECENT_USERS)
        user_storage.pop();
    
    // update storage
    json_users = JSON.stringify(user_storage);
    localStorage.setItem(RECENT_USERS_KEY, json_users);
}