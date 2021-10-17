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
    template: function(element, attrs) {
      return '' +
      '<td>' +
      '  <i ng-if="!toxic" ' +
      '     role="img text" ' +
      '     alt="Safe for {{ animal }}" ' +
      '     aria-label="Safe for {{ animal }}" ' +
      '     class="fa fa-check"></i>' +
      '  <a ng-if="toxic" ' +
      '     tooltip-placement="right" ' +
      '     tooltip="{{ row.clinical_signs }}">' +
      '    <i ' +
      '     role="img text" ' +
      '     alt="Not safe for {{ animal }}: {{ row.clinical_signs }}" ' +
      '     aria-label="Not safe for {{ animal }}: {{ row.clinical_signs }}" ' +
      '     class="fa fa-times"></i>' +
      '  </a>' +
      '</td>';
    },
    scope: true,  // inherited scope
    link: function($scope, element, attrs) {
      $scope.toxic = (attrs.toxic === 'true');
      $scope.animal = attrs.animal;
    },
  };
});
