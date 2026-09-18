var buttonHolders = document.querySelectorAll(".button-holder");

for (const buttonHolder of buttonHolders) {
	var pageTitle = buttonHolder.getAttribute("data-title");
	var pageUrl = buttonHolder.getAttribute("data-url");

	var button = document.createElement("button");
	button.className = "copy-button";
	button.innerText = `Copy link to “${pageTitle}”`;
	button.addEventListener("click", (e) => {
		navigator.clipboard.writeText(pageUrl);
		button.innerText = `Copied link to “${pageTitle}”`;
	});

	buttonHolder.append(button);
}
