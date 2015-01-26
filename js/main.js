var phonecatApp = angular.module('plantToxApp', ['ui.bootstrap']);

phonecatApp.controller('PlantToxCtrl', function ($scope) {
  // Initialize data.
  $scope.rows = json_data.data;  // json_data loaded from json import
  _.each($scope.rows, function(row) {
    row.show = true;
  });
  $scope.no_results = false;

  $scope.rowMatches = function(row, query) {
    return _.any(
      _.filter(
        _.pick(row, ['name', 'scientific_name', 'additional_common_names']),
        function(str) { return str; }
      ),
      function(str) {
        return !str || str.toLowerCase().indexOf(query) > -1;
      }
    );
  };

  // Update rows' "show" attribute.
  // Called on search box change.
  $scope.applySearch = function(query) {
    query = query.toLowerCase();
    _.each($scope.rows, function(row) {
      row.show = $scope.rowMatches(row, query);
    });
    $scope.no_results = !_.any(_.pluck($scope.rows, 'show'));
  };
});

// Display a table cell containing checkmark or X for toxicity.
phonecatApp.directive('checkCell', function() {
  return {
    restrict: 'A',
    replace: true,
    template: function(element, attributes) {
      return '' +
      '<td>' +
      '  <i ng-if="!toxic" ' +
      '     class="fa fa-check"></i>' +
      '  <a ng-if="toxic" ' +
      '     tooltip-placement="right" ' +
      '     tooltip="{{ row.clinical_signs }}">' +
      '    <i class="fa fa-times"></i>' +
      '  </a>' +
      '</td>';
    },
    scope: true,  // inherited scope
    link: function($scope, element, attributes) {
      $scope.toxic = attributes.toxic === 'true';
    },
  };
});
