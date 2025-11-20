# Studio AI Integration Notes

This document outlines how the frontend React application integrates with the backend Python/Flask server within the Studio AI environment.

## Base URL

Within the Studio AI development environment, there is no need to specify a full base URL (like `http://localhost:5000`). The environment automatically proxies requests from the frontend to the backend server.

All API calls from the frontend should use relative paths starting with `/api/`.

- **Example:** To fetch the list of communities, the frontend makes a request to `/api/communities`.

## Headers

For most GET requests, no special headers are required. For POST/PUT requests that send JSON data, the `Content-Type` header must be set to `application/json`.

```javascript
headers: {
  'Content-Type': 'application/json'
}
```

When uploading files (like an audio consultation), a `FormData` object is used. In this case, you **should not** set the `Content-Type` header manually. The browser will automatically set it to `multipart/form-data` with the correct boundary.

## Sample Fetch Requests

Here are examples of the different types of `fetch` calls made from the frontend to the backend.

### 1. GET Request (Fetching communities)

This fetches all community data when the application loads.

```javascript
async function fetchCommunities() {
  try {
    const response = await fetch('/api/communities');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    // Use data.communities to update state
  } catch (error) {
    console.error("Failed to fetch communities:", error);
  }
}
```

### 2. POST Request with JSON (Processing text)

This sends a text transcript to the backend for analysis.

```javascript
async function processText(consultationText) {
  try {
    const response = await fetch('/api/process-text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: consultationText,
        push_to_crm: true // Or false, based on user choice
      }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const results = await response.json();
    // Use results to display recommendations
  } catch (error) {
    console.error("Failed to process text:", error);
  }
}
```

### 3. POST Request with FormData (Uploading audio file)

This uploads a recorded audio file for analysis.

```javascript
async function processAudio(audioFile) {
  try {
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('push_to_crm', 'true'); // FormData values are strings

    const response = await fetch('/api/process-audio', {
      method: 'POST',
      body: formData, // Browser sets Content-Type header automatically
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const results = await response.json();
    // Use results to display recommendations
  } catch (error) {
    console.error("Failed to process audio:", error);
  }
}
```

### 4. PUT Request (Updating a community)

This updates an existing community's data in the database.

```javascript
async function updateCommunity(communityId, communityData) {
  try {
    const response = await fetch(`/api/communities/${communityId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(communityData),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result = await response.json();
    console.log(result.message); // e.g., "Community 1 updated"
    // Refetch community list to update UI
  } catch (error) {
    console.error("Failed to update community:", error);
  }
}
```
