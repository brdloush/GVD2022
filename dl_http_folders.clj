(ns dl-http-folders
  (:require  [babashka.fs :as fs]
             [babashka.pods :as pods]
             [clojure.string :as str]
             [clojure.zip :as z]
             [org.httpkit.client :as http]
             [org.httpkit.sni-client :as sni-client])
  (:import [java.util.concurrent Executors]))

(alter-var-root #'org.httpkit.client/*default-client* (fn [_] sni-client/default-client))

(pods/load-pod 'retrogradeorbit/bootleg "0.1.9")

(require
 '[pod.retrogradeorbit.bootleg.utils :as bootleg]
 '[pod.retrogradeorbit.hickory.select :as s])


(defn fetch-as-hickory [base-url path]
  (let [url (str base-url path)
        _ (println "fetch-as-hickory" url)]
    (-> @(http/get url)
        :body
        (bootleg/convert-to :hickory))))

(defn el->href [el]
  (-> el :attrs :href))

(defn parse-folder-hickory [folder-hickory]
  (let [subdirs (->> (s/select (s/and (s/tag :a)
                                      (s/attr :href #(.endsWith % "/")))
                               folder-hickory)
                     (remove #(str/includes? (str (:content %)) "To Parent Directory"))
                     (map el->href)
                     (map #(-> {:type :dir
                                :path %})))
        files (->> (s/select (s/and (s/tag :a)
                                    (s/attr :href #(not (.endsWith % "/"))))
                             folder-hickory)
                   (map el->href)
                   (map #(-> {:type :file
                              :path %})))]
    (into [] (concat subdirs files))))

(defn fetch-url-items [base-url path]
  (parse-folder-hickory (fetch-as-hickory base-url path)))

(defn is-dir? [{:keys [type]}]
  (= type :dir))

(defn file-zipper [root-httpftp-url input-dir]
  (z/zipper
   is-dir?
   (fn children [node]
     (fetch-url-items root-httpftp-url (:path node)))
   (fn make-node [_ c]
     c)
   input-dir))

(defn find-files-to-download [root-httpftp-url base-path]
  (->> (file-zipper root-httpftp-url {:type :dir, :path base-path})
       (iterate z/next)
       (take-while #(not (z/end? %)))
       (map first)
       (remove is-dir?)))

(defn split-path [file-path]
  (let [splitted (str/split file-path #"/")]
    [(str/join "/" (drop-last splitted))
     (last splitted)]))

(defn download-file [root-httpftp-url base-path {:keys [path]} target-root-dir]
  (let [[dir-path filename] (split-path path)
        response @(http/get (str root-httpftp-url path))
        relative-dir-path (str/replace-first dir-path base-path "")]
    (fs/create-dirs (str target-root-dir relative-dir-path))
    (with-open [fos (->> (str target-root-dir "/" relative-dir-path "/" filename)
                         (java.io.FileOutputStream.)
                         (java.io.BufferedOutputStream.))]
      (let [body-is (:body response)]
        (.transferTo body-is fos)))))


(defn download-files [root-httpftp-url base-path target-dir]
  (let [_ (println "Discovering files to be downloaded")
        files (find-files-to-download root-httpftp-url base-path)
        _ (println "Found" (count files) "files to be downloaded")]
    (time
     (let [total_files (count files)
           count-atom (atom 0)
           report-every 500
           _ (add-watch count-atom
                        :report-finished-files
                        (fn [_ _ _ new-count]
                          (when (= (mod new-count report-every) 0)
                            (println "Downloaded" new-count "files"))
                          (when (= new-count total_files)
                            (println "All files done"))))
           nthreads 50
           pool  (Executors/newFixedThreadPool nthreads)
           tasks (->> files
                      (map (fn [file-item]
                             (fn []
                               (download-file root-httpftp-url base-path file-item target-dir)
                               (swap! count-atom inc)))))]
       (doseq [future (.invokeAll pool tasks)]
         (.get future))
       (.shutdown pool)))))

(let [[root-httpftp-url base-path target-dir] *command-line-args*]
  (if (and root-httpftp-url base-path target-dir)
    (download-files root-httpftp-url base-path target-dir)
    (do
      (println "usage: bb dl_http_folders.clj <root-ftp-url> <base-path> <local-download-folder>")
      (println "\n\nexample: bb dl_http_folders.clj https://portal.cisjr.cz /pub/draha/celostatni/szdc/2022 /tmp/2022"))))
