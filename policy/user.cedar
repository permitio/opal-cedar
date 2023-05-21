// All users can read all resources
permit(
    principal,
    action in Action::"get",
    resource
);