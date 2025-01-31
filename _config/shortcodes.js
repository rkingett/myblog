export default function (eleventyConfig) {
	eleventyConfig.addShortcode("currentBuildDate", () => {
		return new Date().toISOString();
	});

	eleventyConfig.addShortcode("currentBuildYear", () => {
		return new Date().getFullYear();
	});
}
