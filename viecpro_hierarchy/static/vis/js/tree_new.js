function makeTree(data) {
  let displayed_ent = null;
  makeTree.displayed_ent = displayed_ent;
  //let card_selection = d3.select("#selection_card");
  let deltaX;
  let deltaY;
  let slideContainer = d3.select("#slidecontainer");
  let firstCall = true;
  let toolTip = d3.select("#tooltip");
  let textRange = d3.select("#textRange");
  textRange.property("value", 12);
  d3.select("#window_toolbar").style("visibility", "visible");
  let labelTextSize = "12px sans-serif";
  let labelDY = "4px";
  let textFactor = 0;
  let colorLabel;
  let tabButton = d3.select("#graph_selection_tab_style");

  tabButton.style("visibility", "hidden").style("transition", "0s");
  const sleep = (milliseconds) => {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  };

  let labelVisButton = d3.select("#button_hide_labels");
  if (!labelVisState) {
    labelVisButton.html("off");
  } else {
    labelVisButton.html("on");
  }

  let nodeColors = {
    p: "darkgrey",
    i: "steelblue",
    default: "steelblue",
    f: "green",
  };

  try {
    d3.select("#depthSlider").remove();
  } catch {}

  //card_selection.style("visibility", "hidden");

  let thisWidth;
  let thisHeight;
  let dragHandler = d3
    .drag()

    .on("start", function () {
      let dragTarget = d3.select(this);
      thisWidth = parseInt(dragTarget.style("width")) + 16;
      thisHeight = parseInt(dragTarget.style("height")) + 16;
      deltaX = parseInt(dragTarget.style("left")) - d3.event.x;
      deltaY = parseInt(dragTarget.style("top")) - d3.event.y;
    })
    .on("drag", function () {
      let dragTarget = d3.select(this);

      let xpos = deltaX + d3.event.x;
      let ypos = deltaY + d3.event.y;
      let maxX = window.innerWidth - thisWidth;
      let maxY = window.innerHeight - thisHeight;
      let boundx;
      let boundy;
      if (navbarVisible) {
        boundx = xpos > maxX ? maxX : xpos < 16 ? 16 : xpos;
        boundy = ypos > maxY ? maxY : ypos < 215 ? 215 : ypos;
      } else {
        boundx = xpos > maxX ? maxX : xpos < 16 ? 16 : xpos;
        boundy = ypos > maxY ? maxY : ypos < 127 ? 127 : ypos;
      }

      dragTarget.style("top", boundy + "px").style("left", boundx + "px");
    });

  //dragHandler(d3.selectAll(".info_card"));

  if (d3.select("#tree")) {
    d3.select("#tree").selectAll("*").remove();

    makeTree.displayed_ent = null;

    d3.select("#selection_entity").text("");
    d3.select("#selection_pk").text("");

    d3.select("#selection_name").text("");
    d3.select("#selection_start").text("");
    d3.select("#selection_end").text("");
    d3.select("#selection_link").attr("href", "").text("");
  }
  let treeData = JSON.parse(data);
  console.log("treeData", treeData);
  let graph_type = treeData.graph_type;

  treeData = treeData.tree_data;

  let margin = { top: 200, right: 90, bottom: 20, left: 200 };

  let width = 2000;
  let height = 10000;

  let i = 0;
  let duration = 300;
  let root;
  let depth_separation = 300;
  let circleSize = 16;
  let circleSeparation = 10;

  let svg = d3
    .select("#tree")
    .append("svg")
    .attr("viewBox", "-200 -250  1000 800 ")
    .attr("preserveAspectRatio", "xMinYMin meet")
    .call(
      d3.zoom().on("zoom", function () {
        svg.attr("transform", d3.event.transform);
      })
    )
    .append("g");
  d3.select("#tree svg").on("dblclick.zoom", null);
  let treemap = d3
    .tree()
    .nodeSize([circleSize + circleSeparation, circleSize + circleSeparation]); // use nodeSize here
  root = d3.hierarchy(treeData, function (d) {
    return d.children;
  });

  if (horizontal) {
    root.x0 = 0;
    root.y0 = 250;
  } else {
    root.x0 = 250;
    root.y0 = 0;
  }
  update(root);
  textRange.on("input", labelSizeAction);

  function update(source) {
    makeTree.doubleClick = doubleClick;
    makeTree.click = click;
    // makeTree.contractAll = contractAll;
    // makeTree.expandAll = expandAll;

    if (horizontal) {
      treemap = d3
        .tree()
        .nodeSize([
          circleSize + circleSeparation + 20,
          circleSize + circleSeparation + 20,
        ]);
    } else {
      if (labelTextSize.slice(0, 2) > 26) {
        treemap = d3
          .tree()
          .nodeSize([
            circleSize + circleSeparation + 15,
            circleSize + circleSeparation + 15,
          ]);
      } else if (labelTextSize.slice(0, 2) > 18) {
        treemap = d3
          .tree()
          .nodeSize([
            circleSize + circleSeparation + 10,
            circleSize + circleSeparation + 10,
          ]);
      } else {
        treemap = d3
          .tree()
          .nodeSize([
            circleSize + circleSeparation,
            circleSize + circleSeparation,
          ]);
      }
    }

    let treeData = treemap(root);

    makeTree.graphRoot = root.data.meta.label + "_" + graph_type;

    // if (graph_type === "normal") {
    //   graph_type = null;
    // }

    function updateGraphInfo() {
      let table = "#table_graph";
      d3.select(table).selectAll("*").remove();
      display_row(table, "Root", root.data.meta.label);
      display_row(table, "Type", root.data.meta.entity_type);
      display_row(table, "Option", graph_type);
      display_row(table, "Nodes (total)", nodeCount);
      display_row(table, "Nodes (distinct)", distinctSet.size);
      display_row(table, "Start", root.data.meta.start);
      display_row(table, "End", root.data.meta.end);
      display_row(table, "Id", root.data.meta.pk);

      display_row(table, "Link", root.data.meta.url);
    }

    //if (individualNodeColors) {
    showColorExamples();
    if (boxVisibility === "visible") {
      d3.select("#node_color_examples").style("visibility", "visible");
    }

    // }
    // nodes
    let nodes = treeData.descendants();
    let distinctSet = new Set();
    let nodeCount = 0;
    if (horizontal) {
      nodes.forEach(function (d) {
        d.y = d.depth * (depth_separation + textFactor);
        nodeCount += 1;
        distinctSet.add(d.data.meta.pk);
      });
    } else {
      nodes.forEach(function (d) {
        d.y = d.depth * (depth_separation + textFactor);
        nodeCount += 1;
        distinctSet.add(d.data.meta.pk);
      });
    }
    updateGraphInfo();

    let node = svg.selectAll("g.node").data(nodes, function (d) {
      return d.id || (d.id = ++i);
    });
    let nodeEnter = node
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", function (d) {
        if (!d.parent || source !== root) {
          if (horizontal) {
            return "translate(" + source.x0 + ", " + source.y0 + ")";
          } else {
            return "translate(" + source.y0 + ", " + source.x0 + ")";
          }
        } else {
          if (horizontal) {
            return "translate(" + d.parent.x0 + ", " + d.parent.y0 + ")";
          } else {
            return "translate(" + d.parent.y0 + ", " + d.parent.x0 + ")";
          }
        }
      })
      .on("click", makeTree.click)

      .on("dblclick", makeTree.doubleClick);

    nodeEnter
      .append("circle")
      .attr("class", "background")
      .attr("r", 10)
      .style("fill", "white");

    nodeEnter
      .append("circle")
      .attr("class", "node")
      .attr("r", 0)
      .style("fill", function (d) {
        return d._children ? "steelblue" : "#fff";
      });

    let nodeUpdate = nodeEnter.merge(node);

    nodeUpdate
      .transition()
      .duration(duration)
      .attr("transform", function (d) {
        if (horizontal) {
          return "translate(" + d.x + ", " + d.y + ")";
        } else {
          return "translate(" + d.y + ", " + d.x + ")";
        }
      });

    sleep((duration * 2) / 3).then(() => {
      if (horizontal) {
        nodeEnter // todo: change for vertical text display
          .append("text")
          .style("font", labelTextSize)
          .attr("dy", labelDY)
          .attr("text-anchor", function (d) {
            return "end";
            //return d.children || d._children ? "end" : "start";
          })
          .attr("dx", -30)
          .attr("transform", "rotate(300)")
          .text(function (d) {
            return d.data.meta.label;
          });
      } else {
        nodeEnter
          .append("text")
          .style("font", labelTextSize)
          .attr("dy", labelDY)
          .attr("dx", 0)
          .attr("transform", "rotate(0)")

          .attr("x", function (d) {
            //return d.children || d._children ? -13 : 13;
            return 13;
          })
          .attr("text-anchor", function (d) {
            return "start";
            //return d.children || d._children ? "end" : "start";
          })
          .text(function (d) {
            return d.data.meta.label;
          });
      }
    });

    function color_switch(d) {
      // d3.select(d).style("fill-opacity", "30%");

      switch (d.data.meta.entity_type) {
        case "Funktion":
          return nodeColors.f;
        case "Person":
          return nodeColors.p;
        case "Institution":
          return nodeColors.i;
        default:
          return nodeColors.default;
      }
    }
    nodeUpdate
      .select("circle.node")
      .attr("r", 10)
      .style("fill", function (d) {
        let computedColor = color_switch(d);
        d3.select(this).style("fill-opacity", "100%");
        let is_clicked = d.data.meta.pk === makeTree.displayed_ent;

        if (individualNodeColors) {
          if (d._children) {
            return is_clicked ? "red" : computedColor;
          } else {
            d3.select(this).style("fill-opacity", "30%");
          }
          return computedColor;
        } else {
          return d._children ? "steelblue" : "#fff";
        }
      })
      .attr("cursor", "pointer")
      .style("stroke", function (d) {
        if (d.data.meta.pk === makeTree.displayed_ent) {
          return "red";
        } else {
          if (individualNodeColors) {
            return color_switch(d);
          } else {
            return "steelblue";
          }
        }
      });

    if (horizontal) {
      nodeUpdate
        .select("text")
        .style("font", labelTextSize)
        .attr("dy", labelDY)
        .attr("text-anchor", function (d) {
          return "end";
          //return d.children || d._children ? "end" : "start";
        })
        .attr("dx", -30)
        .attr("transform", "rotate(300)");

      nodeEnter.select("text").attr("transform", "rotate(270)");
      // todo: change for vertical display!
    } else {
      nodeUpdate
        .select("text")
        .style("font", labelTextSize)
        .attr("dy", labelDY)
        .attr("x", 13)
        .attr("dx", 0)
        .attr("text-anchor", function (d) {
          return "start";
        })
        .attr("transform", "rotate(0)");
    }

    let nodeExit = node.exit();

    nodeExit.select("text").remove();

    nodeExit
      .transition()
      .duration(duration)
      .attr("transform", function (d) {
        if (!d.parent || source !== root) {
          if (horizontal) {
            return "translate(" + source.x + "," + source.y + ")";
          } else {
            return "translate(" + source.y + "," + source.x + ")";
          }
        } else {
          if (horizontal) {
            return "translate(" + d.parent.x + "," + d.parent.y + ")";
          } else {
            return "translate(" + d.parent.y + "," + d.parent.x + ")";
          }
        }
      })
      .remove();

    nodeExit.select("circle").attr("r", 0);
    nodeExit.select("text").style("fill-opacity", 0);

    // links
    function diagonal(s, d) {
      if (horizontal) {
        path = `M ${s.x} ${s.y}
      C ${s.x} ${(s.y + d.y) / 2} 
        ${d.x} ${(s.y + d.y) / 2} 
        ${d.x} ${d.y}`;
      } else {
        path = `M ${s.y} ${s.x}
      C ${(s.y + d.y) / 2} ${s.x}
        ${(s.y + d.y) / 2} ${d.x}
        ${d.y} ${d.x}`;
      }

      return path;
    }

    let links = treeData.descendants().slice(1);
    let link = svg.selectAll("path.link").data(links, function (d) {
      return d.id;
    });
    let linkEnter = link
      .enter()
      .insert("path", "g")
      .attr("class", "link")
      .attr("d", function (d) {
        let o;
        if (!d.parent || source !== root) {
          if (horizontal) {
            o = { x: source.x0, y: source.y };
          } else {
            o = { x: source.x0, y: source.y };
          }
        } else {
          if (horizontal) {
            o = { x: d.parent.x0, y: d.parent.y };
          } else {
            o = { x: d.parent.x0, y: d.parent.y };
          }
        }
        return diagonal(o, o);
      });
    //todo: link enter: start of transition is set to parent endpoint, should be startpoint of parent and move with parent node.
    let linkUpdate = linkEnter.merge(link);
    linkUpdate
      .transition()
      .duration(duration)
      .attr("d", function (d) {
        return diagonal(d, d.parent);
      });

    let linkExit = link
      .exit()
      .transition()
      .duration(duration)
      .attr("d", function (d) {
        let o;
        if (!d.parent || source !== root) {
          o = { x: source.x, y: source.y };
        } else {
          o = { x: d.parent.x, y: d.parent.y };
        }
        return diagonal(o, o);
      })
      .remove();

    let allNodes = d3.selectAll(".node");

    nodes.forEach(function (d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });

    updateLabelVisibility();

    allNodes
      .on("mouseover", function () {
        d3.select(this).select("text").style("visibility", "visible");
        if (labelHighlight) {
          d3.select(this).select("text").style("font", labelTextSize);
        }
      })
      .on("mouseout", function () {
        if (!labelVisState) {
          d3.select(this).select("text").style("visibility", "hidden");
        }
        d3.select(this).select("text").style("font", labelTextSize);
      });

    let max_depth;
    if (firstCall) {
      max_depth = d3.max(nodes, function (d) {
        return d.depth;
      });
      slideContainer
        .append("input")
        .attr("id", "depthSlider")
        .attr("type", "range")
        .attr("min", "0")
        .attr("max", max_depth)
        .attr("value", max_depth)
        .on("input", slideAction);
      firstCall = false;
    }

    //<input type="range" min="1" max="100" value="50" className="slider" id="myRange">
    function slideAction() {
      let value = this.value;
      allNodes.each(function (d) {
        if (d.depth >= value) {
          if (d.children) {
            d._children = d.children;
            d.children = null;
          }
        } else {
          if (d._children) {
            d.children = d._children;
            d._children = null;
          }
        }
      });
      update(root);
    }

    function showColorExamples() {
      let exampleDiv = d3.select("#node_color_examples");
      //let labelDiv = d3.select("#node_color_label");
      exampleDiv.selectAll("*").remove();
      exampleDiv.append("svg");
      if (boxVisibility === "hidden") {
        d3.select("#node_color_examples").style("visibility", "hidden");
      }
      //labelDiv.append("label").attr("id", "colorTypeLabel");
      //colorLabel = d3.select("#colorTypeLabel");
      let exampleDivSVG = exampleDiv.select("svg");
      exampleDivSVG.on("click", switch_entity_color);

      let p = { type: "Person", c: nodeColors.p };
      let i = { type: "Institution", c: nodeColors.i };
      let f = { type: "Funktion", c: nodeColors.f };
      let u = { type: "Entity or Function", c: nodeColors.i };
      if (!individualNodeColors) {
        circleData = [u];
      } else {
        switch (graph_type) {
          case "add functions":
            circleData = [i, f];
            break;
          case "add functions and persons":
            circleData = [i, f, p];
            break;
          case "show institution hierarchy":
            circleData = [f, i];
            break;
          case "show amt and persons":
            circleData = [f, i, p];
            break;
          case "normal":
            circleData = [p, f, i];
            break;
          default:
            circleData = [i];
            break;
        }
      }

      exampleDivSVG.style(
        "width",
        `${18 * circleData.length + circleData.length * 10}px`
      );
      let circles = exampleDivSVG.selectAll(".dot").data(circleData);

      let w = parseInt(exampleDivSVG.style("width"));
      let h = parseInt(exampleDivSVG.style("height"));

      circles
        .enter()
        .append("circle")
        .attr("class", "dot")

        .attr("cx", function (d) {
          let len = circleData.length;
          let pos = circleData.indexOf(d) + 1;
          let fract = pos / len;
          let delta = w * (1 / len) * 0.5;
          let final = w * fract - delta;
          return `${final}px`;
        })
        .attr("cy", `${h / 2}px`)
        .style("fill", function (d) {
          if (individualNodeColors) {
            return d.c;
          } else {
            return "white";
          }
        })
        .style("fill-opacity", () => {
          return individualNodeColors ? "30%" : "100%";
        })
        .style("stroke", function (d) {
          return d.c;
        })
        .on("mouseover", function (d) {
          if (individualNodeColors) {
            let x = d3.event.pageX + 12;
            let y = d3.event.pageY - 30;

            toolTip.transition().duration(200).style("opacity", 0.95);
            toolTip
              .html(d.type)
              .style("left", x + "px")
              .style("top", y + "px");
          }
        })
        .on("mouseout", function (d) {
          toolTip.transition().duration(300).style("opacity", 0);

          // https://bl.ocks.org/d3noob/a22c42db65eb00d4e369
        });
      exampleDiv.style("visibility", "hidden");
    }

    function updateLabelVisibility() {
      let text_attr = d3.selectAll(".node text");
      let button = d3.select("#button_hide_labels");

      if (labelVisState) {
        text_attr.style("visibility", "visible");
        button.html("on");
      } else {
        text_attr.style("visibility", "hidden");
        button.html("off");
      }
    }

    function doubleClick(d) {
      //card_selection.style("visibility", "hidden");

      makeTree.displayed_ent = null;

      if (d.children) {
        d._children = d.children;
        d.children = null;
      } else {
        d.children = d._children;
        d._children = null;
      }

      update(d);
    }

    function display_row(table, label, data) {
      if (data === "None") {
        data = null;
      }
      if (data) {
        let row = d3.select(table).append("tr");
        row.append("th").attr("class", "toolbar_label").html(label);

        if (label == "Link") {
          row
            .append("td")
            .append("a")
            .attr("href", data)
            .html("Go to Entity")
            .attr("cursor", "pointer");
        } else {
          row.append("td").html(data);
        }
      }
      //el.style("display", () => (data ? "box" : "none"));
      //el.text(data);
    }

    function click(d) {
      let mouse_x = event.pageX;
      let mouse_y = event.pageY;

      if (makeTree.displayed_ent != d.data.meta.pk) {
        async function update_selection() {
          let test = await global_suggestions;

          if (test) {
            let item = test.filter(
              (n) =>
                n.pk === d.data.meta.pk && n.group === d.data.meta.entity_type
            );
            item = item[0];
            input.value = item.label; //item value is array of [e.name, "Institution|Person|Funktion", a.pk]
            selectionDATA = item.value;
            show_graph_options(item.value);
          } else {
            alert("something went wrong");
          }
        }
        showTab("graph_selection_tab");

        update_selection();
        tabButton.style("visibility", "visible").style("transition", "0s");

        makeTree.displayed_ent = d.data.meta.pk;
        let table = "#table_selection";
        let tableSelection = d3.select(table);
        tableSelection.selectAll("*").remove();

        display_row(table, "Name", d.data.meta.label);
        display_row(table, "Type", d.data.meta.entity_type);
        display_row(table, "Start", d.data.meta.start);
        display_row(table, "End", d.data.meta.end);

        display_row(table, "Rel. von", d.data.meta.rel_start);

        display_row(table, "Rel. bis", d.data.meta.rel_end);
        display_row(table, "Id", d.data.meta.pk);

        display_row(table, "Link", d.data.meta.url);

        // d3.select("#selection_pk").text(d.data.meta.pk);
        // d3.select("#selection_start").text(d.data.meta.start);
        // d3.select("#selection_end").text(d.data.meta.end);
        // display_row("#selection_rel_start", d.data.meta.rel_start);
        // //d3.select("#selection_rel_start").text(d.data.meta.rel_start);
        // d3.select("#selection_rel_end").text(d.data.meta.rel_end);
        // d3.select("#selection_link")
        //   .attr("href", d.data.meta.url)
        //   .text("Go to Entity");

        //card_selection.style("visibility", "visible");
      } else {
        input.value = "";
        tabButton.style("visibility", "hidden").style("transition", "0s");
        showTab("graph_info_tab");

        show_graph_options({});
        selectionData = null;

        //card_selection.style("visibility", "hidden");
        makeTree.displayed_ent = null;
      }
      update(root);
      //d3.event.sourceEvent.stopPropagation();
    }
    function switch_entity_color() {
      let colorDiv = d3.select("#node_color_examples");

      if (individualNodeColors) {
        individualNodeColors = false;

        showColorExamples();
        update(root);
      } else {
        individualNodeColors = true;
        d3.select("#button_color_entities").html("on");

        showColorExamples();
        update(root);
      }
    }
    makeTree.switch_entity_color = switch_entity_color;
    updateLabelVisibility();
  }
  function labelSizeAction() {
    let v = this.value;
    labelTextSize = `${v}px sans-serif`;
    let factor = (v - 12) / 6;
    labelDY = `${4 + 2 * factor}px`;
    textFactor = factor * 100;

    update(root);
  }
  function wrapper() {
    let button = d3.select("#button_orientation");
    if (horizontal) {
      button.html("horizontal");
    } else {
      button.html("vertical");
    }
    if (labelVisState) {
      labelVisState = false;
      update(root);
      sleep((duration * 2) / 3).then((d) => {
        switch_label_visibility();
      });
    } else {
      update(root);
    }
  }
  makeTree.update = wrapper;
}
