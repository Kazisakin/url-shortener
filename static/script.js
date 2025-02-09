// Copy-to-clipboard function for the short URL input
function copyToClipboard() {
    var copyText = document.getElementById("shortUrlInput");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices
    navigator.clipboard.writeText(copyText.value).then(function() {
      alert("Copied the URL: " + copyText.value);
    }, function(err) {
      console.error("Failed to copy text: ", err);
    });
  }
  