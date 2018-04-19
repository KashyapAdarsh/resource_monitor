// Get the modal
var modal = document.getElementById('logs');

// Get the button that opens the modal
var startCluster = document.getElementById("startCluster");
var monitorCluster = document.getElementById("monitorCluster");
var cleanUpCluster = document.getElementById("cleanUpCluster");

var configModal = document.getElementById('clusterConfig');

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on the button, open the modal 
startCluster.onclick = function() {
    console.log('Start click clicked');
    console.log(configModal);
    configModal.style.display = "block";
}
monitorCluster.onclick = function() {
    modal.style.display = "block";
}
cleanUpCluster.onclick = function() {
    modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
