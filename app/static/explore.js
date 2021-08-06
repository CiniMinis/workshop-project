function get_more_users() {
    return new Promise((resolve, reject) => {
        var request = $.ajax({
            url: '/api/get_user_deck',
            type: 'GET',
        });
        request.done(resolve);
    });
}


// Restores scroll position on refresh
history.scrollRestoration = "manual";
window.onbeforeunload = () => {
    $(window).scrollTop(0);
};

// When page reaches bottom, load more users
$(window).scroll(function() {
    // check if bottom of page is reached
    if( $(window).scrollTop() == $(document).height() - $(window).height() ) {
        get_more_users()
            .then((new_content) => {
                $("#exploreUserList").append(new_content);
            })
            .then(draw_all_avatars);
    }
});