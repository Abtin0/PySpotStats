// Function to toggle the visibility of the artist lists
function toggleVisibility(artistId) {
    var element = document.getElementById(artistId);
    if (element.style.display === "none") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}
