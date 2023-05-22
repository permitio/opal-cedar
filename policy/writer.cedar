// Writers can perform post and put on artciles
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
) when { resource has published  && resource.published == false };