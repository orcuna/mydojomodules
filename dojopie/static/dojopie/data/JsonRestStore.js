/* Module turnarounds tastypie-dojo json format compatibilty */

define( ['dojo/_base/declare',
         'dojox/data/JsonRestStore'],
        function (declare, JsonRestStore) {
            declare('dojopie.data.JsonRestStore', JsonRestStore, {
                _processResults: function(results, deferred){
                    var count = results.objects.length;
                    return {totalCount: deferred.fullLength ||
                            (deferred.request.count == count ? (deferred.request.start ||
                                                                0) + count * 2 : count),
                            items: results.objects};
                }
            })
        }
)

