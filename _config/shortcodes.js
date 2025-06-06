export default function (eleventyConfig) {
	eleventyConfig.addShortcode("currentBuildDate", () => {
		return new Date().toISOString();
	});

	eleventyConfig.addShortcode("currentBuildYear", () => {
		return new Date().getFullYear();
	});

	eleventyConfig.addShortcode("redirectTo", (destination) => {
		return `<!DOCTYPE html>
<html lang="en-US">
  <meta charset="utf-8" />
  <title>Redirecting&hellip;</title>
  <link rel="canonical" href="${destination}" />
  <script>
    location = '${destination}';
  </script>
  <meta http-equiv="refresh" content="0; url=${destination}" />
  <meta name="robots" content="noindex" />
  <h1>Redirecting&hellip;</h1>
  <a href="${destination}">Click here if you are not redirected.</a>
</html>`;
	});
}
