(function() {

    let dd_options = [
      "Selected Country",
      "Country Currencies",
      "Selected Currency",
      "Countries with Shared Currencies",
    ]

    let width = 970;
    let height = 510;
    let margin = 5;

    let svg = d3.select("#map")
        .classed("svg-container", true)
      .append("svg")
        .attr("preserveAspectRatio", "xMinYMin meet")
        //viewBox values decided manually, not clear how to get these dynamically
        .attr("viewBox", `-${margin} -${margin} ${width} ${height}`)
        .classed("svg-content-responsive", true)

    let gradient = svg.append("defs").append('linearGradient').attr("id", "mainGradient");
    svg.append("rect").classed("blue-clear-red-fade", true).attr("y", "315px").attr("x", "50px");

    gradient.append("stop")
      .classed("stop-red", true)
      .attr('offset', "0");

    gradient.append("stop")
      .classed("stop-clear", true)
      .attr('offset', "0.5");

    gradient.append("stop")
      .classed("stop-blue", true)
      .attr('offset', "1");


    d3.json("/static/country_currency.topo.json")
        .then(ready);

    let projection = d3.geoNaturalEarth1();
    let path = d3.geoPath(projection);

    async function set_rates(curr) {
      color = d3.scaleQuantize([-1, 1], d3.schemeBlues[9])
      let json_data = await fetch(`/rates?card_curr=${curr}`)
        .then(response => response.json())

      d3.selectAll(".country:not(selected)")
        .data(json_data.relative_rates, d => d.id)
        .style("--fill", d => (d.rate < 0) ? "red" : "blue")
        .style("--opacity", d => Math.abs(d.rate))
        .classed("country", false)
        .classed("rated", true)

      let quartiles = json_data.quartiles


      // Consider using color transitions, either linear interpolation between ticks or colours.
      // quartile colour transitions could work well.
      d3.selectAll(".axis").remove();

      var scale = d3.scaleOrdinal()
        .domain([quartiles[0], quartiles[1], quartiles[2], quartiles[3], quartiles[4]])
        .range([0, 25, 50, 75, 100]);

      let relAxis = d3.axisBottom()
        .scale(scale)
        .tickValues(quartiles)
        .tickFormat(d => `${(d*10000).toFixed(0)}`);

      // d3.select("svg").append("g").call(relAxis).classed("axis", true).attr("transform", "translate(150,325)");

      d3.select("svg").insert("g", ".blue-clear-red-fade + *").call(relAxis).classed("axis", true).attr("transform", "translate(150,325)");

      // d3.select(".domain").attr("fill", "black").attr("stroke", "black")
      // d3.select(".tick").attr("fill", "black").attr("stroke", "black")
      // d3.select(".tick line").attr("fill", "black").attr("stroke", "black")
      // d3.select(".tick text").attr("fill", "black").attr("stroke", "black")
    }



    // todo: tidy up state transitions
    // todo: investigate wheter need to rebind data each time
    function ready(data) {

      let graticule = d3.geoGraticule().step([10, 10]);

      svg.selectAll('path.graticule')
          .data([graticule()])
          .enter()
        .append('path').classed('graticule', true)
         .attr('d', path)
         .exit()
         .remove();

        svg.append("path")
            .datum(graticule.outline)
            .attr("class", "graticule outline")
            .attr("d", path);

        let countries = topojson.feature(data, data.objects.countries).features;

        svg.selectAll(".country")
           .data(countries, (d) => d.id)
           .enter()
         .append("path")
           .attr("class", "country")
           .attr("d", path)
           .on('click', function(d) {

                d3.selectAll(".rated")
                  .data(countries, d => d.id)
                    .classed("rated", false)
                    .classed("country", true);

                 let selected = d3.select(this).classed("selected");
                 let currs = d.properties.currencies.map(d => d.code);
                 let currs_bool = {};

                 for (let i = 0; i < currs.length; i++){
                   currs_bool[currs[i]] = true;
                 }

                 d3.selectAll(".same_curr")
                    .classed("same_curr", false);

                 d3.select(".selected")
                    .classed("selected", false);


                 selected = !selected;

                 d3.select(this)
                    .classed("selected", selected);

                 if (selected) {
                   d3.selectAll(".country").data(countries, (d) => d.id).classed(
                      "same_curr",
                      (f) => f.properties.currencies.map(d => d.code).some(x => currs_bool[x]));

                   d3.selectAll(".same_curr").raise();

                   set_rates(currs[0], countries)
                 }
           }
           )
    }
})();