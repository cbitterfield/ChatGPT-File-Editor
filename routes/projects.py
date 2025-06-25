import json
import quart
from quart import Blueprint
from itertools import islice

from project import projects
from utils import file_search

projects_routes = Blueprint('projects', __name__)


@projects_routes.get("/projects/<string:project_name>/files")
async def get_files(project_name):
    print(f'Querying files for project "{project_name}"')
    try:
        project = projects[project_name]
    except KeyError:
        return quart.Response(response=json.dumps({
            "error": f"Project {project_name} not found",
        }), status=404)

    # Generate and cache the file list
    files = list(file_search(project, '*'))
    project.file_cache = files

    print(files[:20])
    print(len(files))

    return quart.Response(response=json.dumps(files), status=200)


@projects_routes.get("/projects/<string:project>/file")
async def get_file(project):
    filename = quart.request.args.get("filename")
    print(f'Querying file "{filename}" for project "{project}"')

    if project not in projects.get_all():
        return quart.Response(response=json.dumps({
            "error": f"Project {project} not found",
        }), status=404)

    file = projects[project].path / filename

    if not file.exists():
        return quart.Response(response=json.dumps({
            "error": f"File {filename} not found",
        }), status=404)

    contents = file.read_text().splitlines()
    contents = [f"{i + 1}: {line}" for i, line in enumerate(contents)]

    return quart.Response(response=json.dumps({
        "full_path": str(file.absolute()),
        "last_modified": file.stat().st_mtime,
        "created": file.stat().st_ctime,
        "contents": contents,
    }), status=200)


@projects_routes.post("/projects/<string:project>/file")
async def set_file_contents(project):
    data = await quart.request.get_json(force=True)
    filename = quart.request.args.get("filename")
    print(f'Setting file "{filename}" for project "{project}"')

    file = projects[project].path / filename
    contents = '\n'.join(data["contents"])

    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(contents)
    return quart.Response(response='OK', status=200)


@projects_routes.put("/projects/<string:project>/file")
async def edit_file(project):
    data = await quart.request.get_json(force=True)
    filename = quart.request.args.get("filename")
    print(f'Editing file "{filename}" for project "{project}"')

    file_path = projects[project].path / filename
    first_line = data["first_line"]
    last_line = data["last_line"]
    content = [f"{line}\n" for line in data["content"]]

    with file_path.open() as f:
        lines = f.readlines()

    lines[first_line - 1:last_line] = content

    with file_path.open('w') as f:
        f.writelines(lines)

    return quart.Response(response='OK', status=200)
