# Nodesets and namespaces

## Problem Description

> Earlier, we had a bug, becuase in our xml we specify `NodeId="ns=1;i=7"`, but in our code we have to
> do `ua.NodeId(7, 2)`. Explain why this is, and suggest an approach to avoid these types of bugs.

## Analysis

The bug occurs because of how OPC UA NodeIds are represented differently in XML vs the asyncua Python
library:

  XML format: ns=1;i=7 means namespace 1, integer identifier 7
  Python asyncua: ua.NodeId(7, 2) means identifier 7, namespace 2

The namespace indices don't match because:

1. XML uses the namespace URI declaration order from the XML file
2. Python asyncua uses the server's runtime namespace table order
3. These can differ, especially when namespaces are added dynamically

Approaches to avoid this bug:

  1. Use namespace URIs instead of indices:

    # Instead of ua.NodeId(7, 2)
    ns_idx = client.get_namespace_index("<http://your-namespace-uri>")
    node_id = ua.NodeId(7, ns_idx)

  2. Create a mapping function:

    def xml_to_asyncua_nodeid(xml_nodeid_str, client):
        # Parse "ns=1;i=7" and convert to proper namespace index
        # Then return ua.NodeId(identifier, resolved_ns_index)

  3. Use string-based NodeIds:

    # asyncua can parse the XML format directly
    node_id = ua.NodeId.from_string("ns=1;i=7")
    # But you still need to resolve the namespace mapping

The most robust approach is #1 - always use namespace URIs rather than indices to avoid namespace
table ordering issues.

> And in the xml - do i have to specify nodeid? Seems error-prone like that.

You don't have to specify NodeIds in XML - the OPC UA specification allows for auto-generation.
Here are your options:

  1. Auto-generated NodeIds (recommended):
  
    ```
    <UAVariable BrowseName="1:nr_actieve_partij" DataType="Int32" ...>
    ```

    The server will auto-assign NodeIds. Much less error-prone.

  2. String-based NodeIds:
  
    ```
    <UAVariable NodeId="ns=1;s=nr_actieve_partij" BrowseName="1:nr_actieve_partij" ...>
    ```

    More readable and stable than numeric IDs.

  3. Keep numeric but use a systematic approach:

        <!-- Use a clear numbering scheme with comments -->
        <!-- Objects: 1000-1999, Variables: 2000-2999 -->
        <UAVariable NodeId="ns=1;i=2001" BrowseName="1:nr_actieve_partij" ...>

Best practice: Use auto-generated NodeIds and reference nodes by BrowseName in your code:

    # Instead of hardcoded NodeId
    node = client.get_node("ns=1;i=7")
    # Use browse path
    node = client.get_objects_node().get_child(["1:PottingLines", "1:Line2", "1:nr_actieve_partij"])

This eliminates the NodeId mismatch issue entirely since you're not hardcoding IDs.
