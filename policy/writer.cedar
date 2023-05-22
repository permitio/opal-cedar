// Writers can perform post and put on artciles
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
) when { principal.karma > 3000 || (context has published  && context.published == false) };