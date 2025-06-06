import requests
import json
import time
from lxml import html

# Configure headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_shared_data(page_content):
    """Extract and parse the _sharedData from Instagram page"""
    try:
        tree = html.fromstring(page_content)
        scripts = tree.xpath('//script[contains(text(), "window._sharedData")]/text()')
        if not scripts:
            return None
            
        script_text = scripts[0].replace("window._sharedData = ", "").rstrip(";")
        return json.loads(script_text)
    except Exception as e:
        print(f"Error parsing shared data: {e}")
        return None

def process_post(url, is_video=False, is_sidecar=False):
    """Process individual post to extract media URLs"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        shared_data = get_shared_data(response.text)
        if not shared_data:
            print(f"Could not get data for post: {url}")
            return None
            
        post_data = shared_data.get('entry_data', {}).get('PostPage', [{}])[0].get('graphql', {}).get('shortcode_media', {})
        
        if is_video:
            return post_data.get('video_url')
        elif is_sidecar:
            edges = post_data.get('edge_sidecar_to_children', {}).get('edges', [])
            return [edge['node']['display_url'] for edge in edges if edge.get('node', {}).get('display_url')]
        else:
            return post_data.get('display_url')
            
    except Exception as e:
        print(f"Error processing post {url}: {e}")
        return None

def get_user_id(username):
    """Get user ID from username by parsing the HTML page."""
    url = f"https://www.instagram.com/{username}/"
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        shared_data = get_shared_data(resp.text)
        if not shared_data:
            return None, None
        user_data = shared_data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
        user_id = user_data.get('id')
        if user_id:
            return user_id, user_data
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching user id: {e}")
        return None, None

def get_all_posts(user_id):
    """Paginate through all posts using Instagram's GraphQL endpoint."""
    posts = []
    has_next_page = True
    end_cursor = ""
    query_hash = "c6809c9c025875ac6f02619eae97a80e"  # public query hash for posts

    while has_next_page:
        variables = {
            "id": user_id,
            "first": 50,
            "after": end_cursor
        }
        url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
        try:
            resp = requests.get(url, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
            media = data["data"]["user"]["edge_owner_to_timeline_media"]
            posts.extend(media["edges"])
            has_next_page = media["page_info"]["has_next_page"]
            end_cursor = media["page_info"]["end_cursor"]
            time.sleep(1)  # be polite to Instagram
        except Exception as e:
            print(f"Error fetching posts: {e}")
            break
    return posts

def main():
    user = input('Input username: ')
    print(f"\nFetching profile: https://www.instagram.com/{user}/")

    user_id, user_data = get_user_id(user)
    if not user_id or not user_data:
        print("Could not find user data. The account might be private or doesn't exist.")
        return

    # Extract basic profile info
    username = user_data.get('username')
    full_name = user_data.get('full_name')
    followers = user_data.get('edge_followed_by', {}).get('count')
    following = user_data.get('edge_follow', {}).get('count')
    post_count = user_data.get('edge_owner_to_timeline_media', {}).get('count')

    print(f"\nProfile Info:")
    print(f"Username: {username}")
    print(f"Full Name: {full_name}")
    print(f"Followers: {followers}")
    print(f"Following: {following}")
    print(f"Total Posts: {post_count}")

    print("\nFetching all posts...")
    start_time = time.time()
    edges = get_all_posts(user_id)

    if not edges:
        print("\nNo posts found or account is private.")
        return

    images = []
    videos = []
    sidecars = []

    for edge in edges:
        node = edge.get('node', {})
        if not node:
            continue

        shortcode = node.get('shortcode')
        typename = node.get('__typename')

        if typename == 'GraphImage':
            images.append(shortcode)
        elif typename == 'GraphVideo':
            videos.append(shortcode)
        elif typename == 'GraphSidecar':
            sidecars.append(shortcode)

    print(f"\nFound {len(images)} images, {len(videos)} videos, {len(sidecars)} sidecar posts")

    # Process image posts
    image_urls = []
    if images:
        print("\nProcessing images...")
        for i, shortcode in enumerate(images, 1):
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"{i}/{len(images)}: {post_url}")
            url = process_post(post_url)
            if url:
                image_urls.append(url)

    # Process video posts
    video_urls = []
    if videos:
        print("\nProcessing videos...")
        for i, shortcode in enumerate(videos, 1):
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"{i}/{len(videos)}: {post_url}")
            url = process_post(post_url, is_video=True)
            if url:
                video_urls.append(url)

    # Process sidecar posts
    sidecar_urls = []
    if sidecars:
        print("\nProcessing sidecar posts...")
        for i, shortcode in enumerate(sidecars, 1):
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            print(f"{i}/{len(sidecars)}: {post_url}")
            urls = process_post(post_url, is_sidecar=True)
            if urls:
                sidecar_urls.extend(urls)

    # Print results
    print("\n" + "="*50)
    print("\nImage URLs:")
    for url in image_urls:
        print(url)

    print("\nVideo URLs:")
    for url in video_urls:
        print(url)

    print("\nSidecar URLs:")
    for url in sidecar_urls:
        print(url)

    elapsed_time = time.time() - start_time
    print(f"\nCompleted in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()