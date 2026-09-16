var buttonHolder = document.getElementById("button-holder");
var pageTitle = buttonHolder.getAttribute("data-title");
var pageUrl = buttonHolder.getAttribute("data-url");

var button = document.createElement("button");
button.id = "copy-link-button";
button.innerText = `Copy link to “${pageTitle}”`;
button.addEventListener("click", (e) => {
	navigator.clipboard.writeText(pageUrl);
	button.innerText = `Copied link to “${pageTitle}”`;
});

buttonHolder.append(button);
