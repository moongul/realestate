import { getCollection } from 'astro:content';

export async function GET() {
	const posts = await getCollection('blog');
	const searchIndex = posts.map((post) => ({
		id: post.id,
		title: post.data.title,
		description: post.data.description,
		category: post.data.category,
		pubDate: post.data.pubDate,
	}));

	return new Response(JSON.stringify(searchIndex), {
		headers: { 'Content-Type': 'application/json' },
	});
}
