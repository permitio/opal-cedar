// Writers can perform post and put on artciles
permit(
    principal,
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
) when (principal in Role::"writer");