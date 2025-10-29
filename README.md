# SocialMediaAPI

REST API generated with MDE Backend Generator.

## Stack

- Java 17 + Spring Boot 3.2.0
- POSTGRESQL database
- Docker Compose ready

## Quick Start

```bash
docker compose up -d --build
```

API available at: `http://localhost:8080`

## Entities

**Users** (9 fields, 8 relationships)  
**UserFollows** (3 fields, 2 relationships)  
**Posts** (7 fields, 4 relationships)  
**Comments** (4 fields, 4 relationships)  
**Likes** (3 fields, 2 relationships)  
**Hashtags** (5 fields, 1 relationships)  
**PostHashtags** (3 fields, 2 relationships)  
**DirectMessages** (5 fields, 2 relationships)  
**Notifications** (5 fields, 1 relationships)  

## API Endpoints

All entities support standard CRUD operations:
- `POST /api/{entity}` - Create
- `GET /api/{entity}` - List all
- `GET /api/{entity}/{id}` - Get by ID
- `PUT /api/{entity}/{id}` - Update
- `DELETE /api/{entity}/{id}` - Delete

- `/api/users` - Users
- `/api/user_follows` - UserFollows
- `/api/posts` - Posts
- `/api/comments` - Comments
- `/api/likes` - Likes
- `/api/hashtags` - Hashtags
- `/api/post_hashtags` - PostHashtags
- `/api/direct_messages` - DirectMessages
- `/api/notifications` - Notifications

## Development

Start database only:
```bash
docker compose up -d postgres```

Run locally:
```bash
mvn spring-boot:run
```

Run tests:
```bash
mvn test
```

Stop services:
```bash
docker compose down -v
```
