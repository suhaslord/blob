document.addEventListener("DOMContentLoaded", function() {
    const backButton = document.getElementById("backButton");
    const forwardButton = document.getElementById("forwardButton");
    const urlInput = document.getElementById("urlInput");
    const goButton = document.getElementById("goButton");
    const contentFrame = document.getElementById("contentFrame");
    const searchButton = document.getElementById("searchButton");
    const searchInput = document.getElementById("searchInput");

    backButton.addEventListener("click", function() {
        contentFrame.contentWindow.history.back();
    });

    forwardButton.addEventListener("click", function() {
        contentFrame.contentWindow.history.forward();
    });

    goButton.addEventListener("click", function() {
        navigate();
    });

    searchButton.addEventListener("click", function() {
        search();
    });

    urlInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            navigate();
        }
    });

    searchInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            search();
        }
    });

    function navigate() {
        let url = urlInput.value.trim();
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "https://" + url;
        }
        contentFrame.src = url;
    }

    function search() {
        let query = searchInput.value.trim();
        if (query !== "") {
            let searchUrl = "https://www.google.com/search?q=" + encodeURIComponent(query);
            contentFrame.src = searchUrl;
        }
    }
});

